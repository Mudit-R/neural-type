"""
Unit Test Suite for Centralized Enterprise Policy Configuration (policy.yaml).
Verifies schema parsing, default fallbacks, application allowlist/denylist rules,
and dynamic integration into AutocorrectService and Global Keyboard Hook.
"""

import os
import pytest
from engine.policy_config import PolicyConfig, DEFAULT_POLICY
from engine.autocorrect_service import AutocorrectService


def test_default_policy_structure():
    """Verifies that default policy fallback has all required keys and defaults."""
    config = PolicyConfig(config_path="non_existent_policy.yaml")
    assert config.is_hook_enabled() is True
    assert config.is_privacy_guard_enabled() is True
    assert config.is_tone_transformation_enabled() is True

    audit_settings = config.get_audit_settings()
    assert audit_settings["retention_days"] == 90
    assert audit_settings["enforce_zero_egress"] is True


def test_app_allowlist_and_denylist_rules():
    """Verifies that denylist and allowlist rules accurately gate applications."""
    config = PolicyConfig()

    # 1. Standard denylist checks (password managers, terminals)
    assert config.is_app_allowed("1password.exe") is False
    assert config.is_app_allowed("keepass.exe") is False
    assert config.is_app_allowed("C:\\Program Files\\1Password\\1password.exe") is False
    assert config.is_app_allowed("cmd.exe") is False
    assert config.is_app_allowed("powershell.exe") is False
    assert config.is_app_allowed("wt.exe") is False

    # 2. Permitted applications
    assert config.is_app_allowed("notepad.exe") is True
    assert config.is_app_allowed("chrome.exe") is True
    assert config.is_app_allowed("winword.exe") is True

    # 3. Custom Allowlist test
    custom_policy = PolicyConfig(config_path="non_existent.yaml")
    custom_policy.policy["hook"]["allowlist"] = ["winword.exe", "outlook.exe"]
    custom_policy.policy["hook"]["denylist"] = ["1password.exe"]

    assert custom_policy.is_app_allowed("winword.exe") is True
    assert custom_policy.is_app_allowed("outlook.exe") is True
    # Denied because not in allowlist
    assert custom_policy.is_app_allowed("notepad.exe") is False
    # Denied by denylist
    assert custom_policy.is_app_allowed("1password.exe") is False


def test_tone_transformation_policy_enforcement():
    """Verifies that AutocorrectService respects enterprise tone policy restrictions."""
    # Policy with tone transformation completely disabled
    disabled_policy = PolicyConfig(config_path="non_existent.yaml")
    disabled_policy.policy["tone_transformation"]["enabled"] = False

    service = AutocorrectService(policy=disabled_policy)
    raw_draft = "hey team, gotta finish asap. thx"
    result = service.transform_tone(raw_draft, mode="professional")
    # Must remain unmodified when blocked by policy
    assert result == raw_draft

    # Policy with only "professional" allowed, but "casual" blocked
    restricted_policy = PolicyConfig(config_path="non_existent.yaml")
    restricted_policy.policy["tone_transformation"]["enabled"] = True
    restricted_policy.policy["tone_transformation"]["allowed_modes"] = ["professional"]

    service_restricted = AutocorrectService(policy=restricted_policy)
    res_prof = service_restricted.transform_tone(raw_draft, mode="professional")
    assert "Hello," in res_prof

    res_cas = service_restricted.transform_tone("Please find attached", mode="casual")
    assert res_cas == "Please find attached"  # Blocked mode returns unmodified


def test_service_policy_yaml_loading(tmp_path):
    """Verifies that custom policy YAML files are parsed and applied to AutocorrectService."""
    custom_yaml = tmp_path / "custom_policy.yaml"
    custom_yaml.write_text(
        """
hook:
  enabled: false
privacy_guard:
  enabled: true
  vertical_profile: "legal"
audit_logging:
  retention_days: 120
autocorrect:
  confidence_threshold: 0.72
""",
        encoding="utf-8",
    )

    policy = PolicyConfig(config_path=str(custom_yaml))
    assert policy.is_hook_enabled() is False
    assert policy.get_active_vertical_profile() == "legal"
    assert policy.get_audit_settings()["retention_days"] == 120

    service = AutocorrectService(policy=policy)
    assert service.confidence_threshold == 0.72
    assert service.privacy_guard.vertical_profile == "legal"
    assert service.audit_logger.retention_days == 120
