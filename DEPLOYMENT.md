# Enterprise Deployment & Management Guide

This document outlines the standardization, packaging, mass deployment, and policy management workflows for **Neural-Type** across regulated enterprise environments.

---

## 1. Overview & Architecture

Neural-Type is an endpoint-resident typing intelligence agent engineered with an **air-gapped, zero-data-egress architecture**:
- **Execution Boundary**: All neural scoring, candidate generation, PII detection, and tone transforms execute strictly in local memory (`127.0.0.1` / endpoint CPU & NPU).
- **Outbound Network Traffic**: `0 bytes`. No telemetry, no cloud LLM API roundtrips, no remote logging.
- **Centralized Configuration**: Controlled by IT admins through a declarative schema (`policy.yaml`) distributed to `%ProgramData%\NeuralType\policy.yaml`.

---

## 2. System Requirements

| Specification | Requirement |
| :--- | :--- |
| **Operating System** | Windows 10 (version 1903+) or Windows 11 (64-bit) |
| **Hardware Acceleration** | DirectML-compatible NPU (Intel AI Boost, AMD Ryzen AI) or DirectX 12 GPU; fallback to CPU AVX2/AVX-512 |
| **Memory Footprint** | ~48 MB RAM runtime allocation |
| **Disk Footprint** | ~35 MB installed (includes INT8 quantized ONNX weights and tokenizer) |
| **Privileges** | Administrative privileges required for machine-wide (`/ALLUSERS=1`) installation |

---

## 3. Silent Mass-Installation Commands

Neural-Type installers support standard enterprise silent execution switches for zero-touch deployment:

### Executable Installer (`Neural-Type-Setup-1.0.0.exe`)

```cmd
:: Silent Machine-Wide Installation (Recommended for Intune / SCCM)
Neural-Type-Setup-1.0.0.exe /S /ALLUSERS=1

:: Silent Machine-Wide Uninstallation
"%ProgramFiles%\Neural-Type\uninstall.exe" /S
```

### Windows Installer Package (`Neural-Type.msi`)

```cmd
:: Silent MSI Installation
msiexec /i "Neural-Type.msi" /qn /norestart ALLUSERS=1

:: Silent MSI Uninstallation
msiexec /x "Neural-Type.msi" /qn /norestart
```

---

## 4. Microsoft Intune Deployment Workflow

Enterprise IT administrators can deploy Neural-Type to all corporate endpoints via **Microsoft Intune (Endpoint Manager)** using the Win32 App format.

### Step 1: Package with `IntuneWinAppUtil.exe`

Download the Microsoft Win32 Content Prep Tool and package the installer:

```cmd
IntuneWinAppUtil.exe -c dist\installer -s Neural-Type-Setup-1.0.0.exe -o dist\intune
```

This produces `Neural-Type-Setup-1.0.0.intunewin`.

### Step 2: Configure Intune App Profile

1. In Microsoft Intune admin center, navigate to **Apps** > **Windows** > **Add** > **Windows app (Win32)**.
2. Upload `Neural-Type-Setup-1.0.0.intunewin`.
3. Configure **Program Information**:
   - **Install command**: `Neural-Type-Setup-1.0.0.exe /S /ALLUSERS=1`
   - **Uninstall command**: `"%ProgramFiles%\Neural-Type\uninstall.exe" /S`
   - **Install behavior**: `System`
   - **Device restart behavior**: `No specific action`
   - **Return codes**: `0` (Success), `3010` (Success with reboot)
4. Configure **Requirements**:
   - **Operating system architecture**: `64-bit`
   - **Minimum OS**: `Windows 10 1903`
5. Configure **Detection Rules**:
   - **Rule type**: `Registry`
   - **Key path**: `HKEY_LOCAL_MACHINE\Software\Microsoft\Windows\CurrentVersion\Uninstall\Neural-Type`
   - **Value name**: `DisplayVersion`
   - **Detection method**: `Version comparison`
   - **Operator**: `Greater than or equal to`
   - **Value**: `1.0.0`

---

## 5. System Center Configuration Manager (SCCM / MECM)

For on-premises deployment via Microsoft Configuration Manager:
1. Create a new **Application** in the Software Library.
2. Select **Manually specify the application information**.
3. Add a **Script Installer** deployment type.
4. Set **Installation program**: `Neural-Type-Setup-1.0.0.exe /S /ALLUSERS=1`
5. Set **Uninstall program**: `"%ProgramFiles%\Neural-Type\uninstall.exe" /S`
6. Set **Installation behavior**: `Install for system`
7. Detection Method: File System check for `%ProgramFiles%\Neural-Type\engine\autocorrect_service.py`.

---

## 6. Centralized Policy Distribution (GPO & Intune)

Corporate IT administrators can enforce endpoint compliance policies by pushing `policy.yaml` to the standard enterprise path:

```
%ProgramData%\NeuralType\policy.yaml
```

When present, this file takes precedence over user configurations.

### Key Policy Controls:

```yaml
# Control where Neural-Type is permitted to operate
hook:
  enabled: true
  # Denylist sensitive tools (e.g. password managers, terminals)
  denylist:
    - "1password.exe"
    - "keepass.exe"
    - "bitwarden.exe"
    - "wt.exe"
    - "cmd.exe"
    - "powershell.exe"

# Configure vertical compliance profiles
privacy_guard:
  enabled: true
  vertical_profile: "healthcare" # Options: "general", "healthcare", "legal", "financial", "all"
  auto_redact_on_commit: false

# Compliance audit evidence retention
audit_logging:
  enabled: true
  retention_days: 90
  max_file_size_mb: 10
  enforce_zero_egress: true
```

### Policy Deployment Options:
- **Group Policy (GPO)**: Computer Configuration > Preferences > Windows Settings > Files (Copy `policy.yaml` to `C:\ProgramData\NeuralType\policy.yaml`).
- **Intune PowerShell Script**: Push `policy.yaml` to endpoints using a platform script executed as `System`.

---

## 7. Authenticode Code Signing

To prevent Windows SmartScreen prompts and enforce software authenticity, the installer and binaries should be signed with an enterprise EV (Extended Validation) code-signing certificate or Azure Trusted Signing:

```cmd
signtool.exe sign /v /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /f "Certificates\EnterpriseSigning.pfx" /p "<PASSWORD>" "dist\installer\Neural-Type-Setup-1.0.0.exe"
```

Verify signature:
```cmd
signtool.exe verify /pa /v "dist\installer\Neural-Type-Setup-1.0.0.exe"
```

---

## 8. Network Egress Security Verification

Security and SOC teams can independently audit the zero-egress claim:
1. Run the built-in isolation verification suite:
   ```cmd
   .venv\Scripts\python -m pytest tests/test_network_isolation.py -v
   ```
2. Monitor the endpoint process via Windows Defender Firewall with Advanced Security / Sysmon / Wireshark to confirm zero TCP/UDP connections to external IPs.
