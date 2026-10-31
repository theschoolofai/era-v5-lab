#!/usr/bin/env python3
import subprocess
import sys

# Critical XID errors that indicate fatal GPU/hardware failure (e.g., XID 79 = GPU fallen off the bus)
CRITICAL_XIDS = {31, 43, 45, 62, 69, 74, 79, 92, 119}

def scan_kernel_logs():
    print("Scanning system kernel logs (dmesg) for NVIDIA XID errors...")
    try:
        result = subprocess.run(["dmesg"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        logs = result.stdout
    except Exception as e:
        print(f"[WARNING] Could not read dmesg logs: {e}")
        return

    detected_critical = False
    for line in logs.splitlines():
        if "NVRM" in line and "Xid" in line:
            print(f"[ALERT] Found: {line}")
            for xid in CRITICAL_XIDS:
                if f"Xid (PCI:{xid})" in line or f"Xid: ?{xid}?" in line or f"Xidకుడు {xid}" in line or f"Xid {xid}" in line:
                    print(f"[CRITICAL ERROR] Fatal NVIDIA XID {xid} detected!")
                    detected_critical = True

    if detected_critical:
        print("[ABORT] Fatal hardware/kernel XID error identified. Halting training job.")
        sys.exit(1)
    else:
        print("[OK] No critical NVIDIA XID errors found in kernel logs.")

if __name__ == "__main__":
    scan_kernel_logs()