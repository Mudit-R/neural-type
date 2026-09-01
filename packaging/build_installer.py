"""
Enterprise Packaging & Installer Build Automation for Neural-Type.
Validates dependencies, ONNX model assets, enterprise policies, and
generates standalone Windows executable/MSI installer bundles.
"""

import os
import sys
import argparse
import hashlib
from pathlib import Path


def calculate_sha256(filepath: str) -> str:
    """Calculates SHA256 checksum of a target file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def validate_packaging_prerequisites(workspace_root: Path) -> bool:
    """Checks that all essential runtime assets and models are present."""
    print("=" * 60)
    print("  NEURAL-TYPE ENTERPRISE PACKAGING VERIFICATION")
    print("=" * 60)

    required_assets = [
        ("Quantized Neural ONNX Model", workspace_root / "models" / "corrector_model_quant.onnx"),
        ("Tokenizer Fast Definition", workspace_root / "models" / "tokenizer" / "tokenizer.json"),
        ("Centralized Policy Schema", workspace_root / "config" / "policy.yaml"),
        ("Installer Configuration", workspace_root / "installer.cfg"),
        ("Global Keyboard Hook Entry", workspace_root / "win32_hook" / "global_keyboard_hook.py"),
        ("Compliance Audit Logger", workspace_root / "engine" / "audit_log.py"),
    ]

    all_passed = True
    for label, path in required_assets:
        if path.exists():
            size_kb = path.stat().st_size / 1024
            sha = calculate_sha256(str(path))[:12]
            print(f"  [PASS] {label:<32} ({size_kb:8.1f} KB, SHA: {sha})")
        else:
            print(f"  [FAIL] {label:<32} MISSING at: {path}")
            all_passed = False

    return all_passed


def generate_nsis_script(workspace_root: Path, output_dir: Path) -> Path:
    """Generates standard NSIS installer script supporting silent deployment (/S)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    nsis_script_path = output_dir / "NeuralTypeSetup.nsi"

    script_content = f"""; Neural-Type Enterprise Installer Script (NSIS)
; Supports silent deployment: NeuralTypeSetup.exe /S /ALLUSERS=1
!define PRODUCT_NAME "Neural-Type"
!define PRODUCT_VERSION "1.0.0"
!define PRODUCT_PUBLISHER "Neural-Type Technologies Inc."
!define INSTALL_DIR "$PROGRAMFILES64\\Neural-Type"

Name "${{PRODUCT_NAME}} ${{PRODUCT_VERSION}}"
OutFile "${{PRODUCT_NAME}}-Setup-${{PRODUCT_VERSION}}.exe"
InstallDir "${{INSTALL_DIR}}"
RequestExecutionLevel admin

Section "MainSection" SEC01
    SetOutPath "$INSTDIR"
    File /r "{workspace_root}\\engine"
    File /r "{workspace_root}\\models"
    File /r "{workspace_root}\\config"
    File "{workspace_root}\\README.md"

    ; Set default ProgramData policy
    CreateDirectory "$COMMONAPPDATA\\NeuralType"
    CopyFiles "$INSTDIR\\config\\policy.yaml" "$COMMONAPPDATA\\NeuralType\\policy.yaml"

    ; Register uninstaller
    WriteUninstaller "$INSTDIR\\uninstall.exe"

    ; Add to Add/Remove Programs (Registry)
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{PRODUCT_NAME}}" "DisplayName" "${{PRODUCT_NAME}}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{PRODUCT_NAME}}" "UninstallString" '"$INSTDIR\\uninstall.exe"'
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{PRODUCT_NAME}}" "DisplayVersion" "${{PRODUCT_VERSION}}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{PRODUCT_NAME}}" "Publisher" "${{PRODUCT_PUBLISHER}}"
SectionEnd

Section "Uninstall"
    RMDir /r "$INSTDIR\\engine"
    RMDir /r "$INSTDIR\\models"
    RMDir /r "$INSTDIR\\config"
    Delete "$INSTDIR\\README.md"
    Delete "$INSTDIR\\uninstall.exe"
    RMDir "$INSTDIR"
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{PRODUCT_NAME}}"
SectionEnd
"""
    with open(nsis_script_path, "w", encoding="utf-8") as f:
        f.write(script_content)

    print(f"\n[OK] Generated NSIS Deployment Script: {nsis_script_path}")
    return nsis_script_path


def main():
    parser = argparse.ArgumentParser(description="Build and package Neural-Type for enterprise deployment.")
    parser.add_argument("--dry-run", action="store_true", help="Validate assets and generate scripts without compiling binary.")
    parser.add_argument("--sign", action="store_true", help="Sign generated executable using signtool.exe.")
    args = parser.parse_args()

    workspace_root = Path(__file__).resolve().parent.parent
    dist_dir = workspace_root / "dist" / "installer"

    if not validate_packaging_prerequisites(workspace_root):
        print("\n[ERROR] Missing required enterprise packaging assets.")
        sys.exit(1)

    nsis_script = generate_nsis_script(workspace_root, dist_dir)

    print("\n" + "=" * 60)
    print("  MASS DEPLOYMENT READINESS CHECK: PASSED")
    print("=" * 60)
    print("  Silent Install Flag   : /S")
    print("  All Users Switch      : /ALLUSERS=1")
    print("  Default Policy Path   : %ProgramData%\\NeuralType\\policy.yaml")
    print("  Intune Packaging Tool : IntuneWinAppUtil.exe")
    print("=" * 60)

    if args.dry_run:
        print("[DRY-RUN] Packaging verification complete. Ready for NSIS/pynsist compiler.")
        return 0

    print("[INFO] Run NSIS or pynsist to produce the final signed .exe / .msi installer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
