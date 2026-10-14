#!/usr/bin/env python3
"""HARMLESS ransomware behaviour simulator for the Wazuh demo (Windows host with the Wazuh agent).

It only creates, overwrites and renames its OWN dummy files inside C:\\SIL-RansomTest, then
writes a fake ransom note. Nothing else on the machine is touched. Expected Wazuh alerts:
  100200 mass file modification, 100201 encrypted-extension files, 100202 shadow-copy deletion command
The shadow-copy step only ECHOES the command text (Sysmon records the command line; nothing is deleted).
"""
import argparse
import pathlib
import platform
import secrets
import subprocess
import time

parser = argparse.ArgumentParser()
parser.add_argument("--dir", default=r"C:\SIL-RansomTest")
parser.add_argument("--files", type=int, default=60)
parser.add_argument("--skip-vss", action="store_true", help="skip the harmless shadow-copy command echo")
args = parser.parse_args()

root = pathlib.Path(args.dir)
root.mkdir(parents=True, exist_ok=True)
print(f"[1/4] creating {args.files} dummy files in {root}")
for i in range(args.files):
    (root / f"patient_note_{i:03}.docx").write_text("synthetic note - SIL assessment simulation")

print("[2/4] waiting 20 s so Wazuh file integrity monitoring records them")
time.sleep(20)

print("[3/4] 'encrypting': overwriting with random bytes and renaming to .locked")
for f in sorted(root.glob("patient_note_*.docx")):
    f.write_bytes(secrets.token_bytes(2048))
    f.rename(f.with_name(f.name + ".locked"))
(root / "HOW_TO_DECRYPT.txt").write_text("SIMULATION ONLY - SIL Infosec assessment. No files were harmed.")

if not args.skip_vss and platform.system() == "Windows":
    print("[4/4] echoing (NOT running) a shadow-copy deletion command for Sysmon to record")
    subprocess.run(["cmd.exe", "/c", "echo", "vssadmin", "delete", "shadows", "/all", "/quiet"], check=False)
else:
    print("[4/4] skipped shadow-copy echo")

print("Done. Check the Wazuh dashboard for rules 100200-100202. Clean up: delete", root)
