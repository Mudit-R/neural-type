"""
Centralized Policy Configuration Loader for NeuraType Enterprise Deployments.
Loads and validates enterprise policies from config/policy.yaml or system-level paths.
"""

import os
import sys
from typing import Dict, Any, List, Optional

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


DEFAULT_POLICY: Dict[str, Any] = {
    "hook": {
        "enabled": True,
        "toggle_hotkey": "<ctrl>+<alt>+a",
        "kill_hotkey": "<ctrl>+<alt>+q",
        "revert_key": "tab",
        "denylist": [
            "1password.exe",
            "bitwarden.exe",
            "keepass.exe",
            "lastpass.exe",
            "cmd.exe",
            "powershell.exe",
            "pwsh.exe",
            "wt.exe",
            "bash.exe",
            "mintty.exe",
            "putty.exe",
        ],
        "allowlist": [],
    },
    "privacy_guard": {
        "enabled": True,
        "vertical_profile": "general",
        "action": "redact",
        "detectors": {
            "ssn": True,
            "credit_card": True,
            "api_keys": True,
            "aws_keys": True,
            "github_tokens": True,
            "iban": True,
            "medical_mrn": False,
            "icd10": False,
            "case_citation": False,
            "cusip": False,
            "swift_bic": False,
        },
    },
    "tone_transformation": {
        "enabled": True,
        "allowed_modes": ["professional", "casual", "concise"],
    },
    "audit_logging": {
        "enabled": True,
        "log_dir": "audit_logs",
        "filename": "audit_trail.jsonl",
        "retention_days": 90,
        "max_file_size_mb": 10,
        "enforce_zero_egress": True,
    },
    "autocorrect": {
        "confidence_threshold": 0.95,
        "revert_timeout_seconds": 3.5,
        "max_edit_distance": 2,
    },
}


class PolicyConfig:
    """
    Centralized policy manager for enterprise IT standardization.
    Controls application boundaries, compliance scanning, and privacy filters.
    """

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._resolve_default_path()
        self.policy: Dict[str, Any] = self._load_policy()

    def _resolve_default_path(self) -> str:
        """Finds policy file from workspace config, bundle, or system ProgramData."""
        # 1. Check Windows ProgramData (standard Intune/GPO deployment directory)
        program_data = os.environ.get("ProgramData", r"C:\ProgramData")
        for candidate_name in ["NeuraType", "NeuralType"]:
            enterprise_cfg = os.path.join(program_data, candidate_name, "policy.yaml")
            if os.path.exists(enterprise_cfg):
                return enterprise_cfg

        # 2. Check bundled frozen path if running as compiled binary
        if getattr(sys, "frozen", False):
            candidate_dirs = [
                getattr(sys, "_MEIPASS", ""),
                os.path.join(getattr(sys, "_MEIPASS", ""), "_internal"),
                os.path.dirname(sys.executable),
                os.path.join(os.path.dirname(sys.executable), "_internal"),
            ]
            for c in candidate_dirs:
                if c:
                    cfg = os.path.join(c, "config", "policy.yaml")
                    if os.path.exists(cfg):
                        return cfg

        # 3. Check workspace config/policy.yaml
        workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        workspace_cfg = os.path.join(workspace_dir, "config", "policy.yaml")
        if os.path.exists(workspace_cfg):
            return workspace_cfg

        return workspace_cfg

    def _load_policy(self) -> Dict[str, Any]:
        """Loads and parses YAML policy, falling back safely to defaults."""
        if not os.path.exists(self.config_path) or not YAML_AVAILABLE:
            return DEFAULT_POLICY.copy()

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f)
                if isinstance(loaded, dict):
                    # Deep merge with defaults to ensure all keys exist
                    merged = DEFAULT_POLICY.copy()
                    for key, val in loaded.items():
                        if isinstance(val, dict) and key in merged and isinstance(merged[key], dict):
                            merged[key] = {**merged[key], **val}
                        else:
                            merged[key] = val
                    return merged
        except Exception:
            pass

        return DEFAULT_POLICY.copy()

    # --- Hook & Application Targeting Policy ---
    def is_hook_enabled(self) -> bool:
        """Returns True if the global keyboard hook is allowed to run."""
        return bool(self.policy.get("hook", {}).get("enabled", True))

    def is_app_allowed(self, process_name_or_title: str) -> bool:
        """
        Determines whether typing assistance is permitted in the given application.
        Evaluates denylist first, followed by allowlist rules.
        """
        if not process_name_or_title:
            return True

        target = process_name_or_title.strip().lower()
        hook_cfg = self.policy.get("hook", {})
        denylist: List[str] = [d.lower() for d in hook_cfg.get("denylist", [])]
        allowlist: List[str] = [a.lower() for a in hook_cfg.get("allowlist", [])]

        # 1. Denylist check: If process matches any denied pattern, strictly block
        for denied in denylist:
            if denied in target or target == denied:
                return False

        # 2. Allowlist check: If allowlist is non-empty, process MUST match
        if allowlist:
            matched = any(allowed in target or target == allowed for allowed in allowlist)
            return matched

        return True

    # --- Privacy Guard Policy ---
    def is_privacy_guard_enabled(self) -> bool:
        """Returns True if on-device PII scanning is enabled."""
        return bool(self.policy.get("privacy_guard", {}).get("enabled", True))

    def get_active_vertical_profile(self) -> str:
        """Returns the active vertical profile ('all', 'general', 'healthcare', 'legal', 'financial')."""
        return str(self.policy.get("privacy_guard", {}).get("vertical_profile", "all")).lower()

    def is_detector_enabled(self, detector_name: str) -> bool:
        """Checks if an individual PII detector rule is enabled."""
        detectors = self.policy.get("privacy_guard", {}).get("detectors", {})
        return bool(detectors.get(detector_name, True))

    def auto_redact_on_commit(self) -> bool:
        """Checks if automatic redaction should be applied on word commit."""
        return bool(self.policy.get("privacy_guard", {}).get("auto_redact_on_commit", False))

    # --- Tone Transformation Policy ---
    def is_tone_transformation_enabled(self) -> bool:
        """Checks if tone transformation is permitted by corporate policy."""
        return bool(self.policy.get("tone_transformation", {}).get("enabled", True))

    def is_tone_mode_allowed(self, mode: str) -> bool:
        """Checks if a specific tone transformation mode (e.g. 'professional') is permitted."""
        if not self.is_tone_transformation_enabled():
            return False
        allowed = self.policy.get("tone_transformation", {}).get("allowed_modes", ["professional", "casual", "concise"])
        return mode.lower() in [m.lower() for m in allowed]

    # --- Audit Logging Policy ---
    def get_audit_settings(self) -> Dict[str, Any]:
        """Returns compliance audit logging parameters."""
        cfg = self.policy.get("audit_logging", {})
        return {
            "enabled": bool(cfg.get("enabled", True)),
            "log_dir": str(cfg.get("log_dir", "audit_logs")),
            "filename": str(cfg.get("filename", "audit_trail.jsonl")),
            "retention_days": int(cfg.get("retention_days", 90)),
            "max_file_size_bytes": int(cfg.get("max_file_size_mb", 10)) * 1024 * 1024,
            "enforce_zero_egress": bool(cfg.get("enforce_zero_egress", True)),
        }

    # --- Autocorrect Tuning ---
    def get_autocorrect_settings(self) -> Dict[str, Any]:
        """Returns core engine hyperparameters."""
        cfg = self.policy.get("autocorrect", {})
        return {
            "confidence_threshold": float(cfg.get("confidence_threshold", 0.95)),
            "revert_timeout_seconds": float(cfg.get("revert_timeout_seconds", 3.5)),
            "max_edit_distance": int(cfg.get("max_edit_distance", 2)),
        }
