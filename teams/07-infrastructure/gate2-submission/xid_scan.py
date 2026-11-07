#!/usr/bin/env python3
import subprocess
import sys
import re

# Critical XID errors that indicate fatal GPU/hardware failure (e.g., XID 79 = GPU fallen off the bus)
CRITICAL_XIDS = {31, 43, 45, 62, 69, 74, 79, 92, 119}

def critical_xids(logs):
    pattern = re.compile(r'\bXid\s*(?:\([^)]*\))?\s*:\s*(\d+)\b')
    return [int(match.group(1)) for line in logs.splitlines() if 'NVRM' in line
            for match in pattern.finditer(line) if int(match.group(1)) in CRITICAL_XIDS]

def scan_kernel_logs():
    print("Scanning system kernel logs (dmesg) for NVIDIA XID errors...")
    try:
        result = subprocess.run(["dmesg"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        logs = result.stdout
    except Exception as e:
        print(f"[WARNING] Could not read dmesg logs: {e}")
        return 2  # Unknown is not a clean scan.

    detected_critical = False
    for line in logs.splitlines():
        if "NVRM" in line and "Xid" in line:
            print(f"[ALERT] Found: {line}")
            for xid in critical_xids(line):
                    print(f"[CRITICAL ERROR] Fatal NVIDIA XID {xid} detected!")
                    detected_critical = True

    if detected_critical:
        print("[ABORT] Fatal hardware/kernel XID error identified. Halting training job.")
        return 1
    else:
        print("[OK] No critical NVIDIA XID errors found in kernel logs.")
        return 0

if __name__ == "__main__":
    sys.exit(scan_kernel_logs())
