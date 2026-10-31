#!/usr/bin/env python3
"""pudding preflight: consistency checks between board.toml, dts, and known hardware facts."""
import re, sys, pathlib, os

root = pathlib.Path(__file__).resolve().parent.parent
errors = []

# board.toml lives in the device repository, never in the assembled tree (the tree only
# carries drivers/kits/patches/scripts/package). Resolution order when run from tree/scripts/:
# 1) the repo itself (developer run), 2) UNIXNU_DEVICE, 3) UniXNU checkout's out/state.json
#    (unixnu remembers -D there), 4) ../<device> relative to the UniXNU checkout.
candidates = [root, root.parent]
env_device = os.environ.get("UNIXNU_DEVICE")
if env_device:
    candidates.append(pathlib.Path(env_device).resolve())
# tree = <uniXNU>/out/<device>/<profile>/<device>/tree -> UniXNU checkout is root.parents[4]
if len(root.parents) > 4:
    unixnu_root = root.parents[4]
    state = unixnu_root / "out" / "state.json"
    if state.is_file():
        try:
            import json
            candidates.append(pathlib.Path(json.loads(state.read_text())["device"]))
        except Exception:
            pass
    candidates.append(unixnu_root.parent / "UniXNU-pudding")
device_root = next((c for c in candidates if (c / "board.toml").is_file()), None)
if device_root is None:
    print("check-pudding: cannot locate the device repository (board.toml) from", root)
    sys.exit(1)
root = device_root
board = (root / "board.toml").read_text(encoding="utf-8")
dts = (root / "dts" / "pudding.dts").read_text(encoding="utf-8")

# 1. splash_region must match the three-way-verified value
m = re.search(r'splash@fc800000 \{[^}]*reg = <0x0 0xfc800000 0x0 0x2b00000>', dts, re.S)
if not m:
    errors.append("dts: splash_region reg must be 0xfc800000/0x2b00000 (three-way verified)")
m = re.search(r'"0x0", "0xfc800000", "0x0", "0x2b00000"', board)
if not m:
    errors.append("board.toml bootimg.dtb_node splash reg must match 0xfc800000/0x2b00000")

# 2. dram_size and owned_memory_size must agree
ds = re.search(r'dram_size = "0x([0-9a-f]+)"', board)
os_ = re.search(r'owned_memory_size = "0x([0-9a-f]+)"', board)
if ds and os_ and ds.group(1) != os_.group(1):
    errors.append("board.toml: dram_size and owned_memory_size disagree")

# 3. memory node in dts must match dram window (name is the low 32 bits: node@<base & 0xffffffff>)
m = re.search(r'memory@([0-9a-f]+) \{[^}]*reg = <0x([0-9a-f]+) 0x([0-9a-f]+) 0x([0-9a-f]+) 0x([0-9a-f]+)>', dts, re.S)
if m:
    base_hi, base_lo = int(m.group(2), 16), int(m.group(3), 16)
    if ((base_hi << 32) | base_lo) & 0xFFFFFFFF != int(m.group(1), 16):
        errors.append("dts: memory node name and reg base disagree")

# 4. REQUIRED_ placeholders must not survive to a build
for f, blob in (("board.toml", board),):
    if "REQUIRED_AFTER_FIRST_FORMAT" in blob:
        print(f"note: {f}: root_match_volume_uuid still a placeholder (expected until first format)")
    if "REQUIRED_SOC_COMMIT" in (root / "feeds.toml").read_text(encoding="utf-8"):
        print("note: feeds.toml: soc commit still a placeholder (expected until repo publication)")

# 5. userdata GPT still unmeasured -> warn loudly before any write-capable payload
if re.search(r'first_lba = 0\b', board):
    print("WARNING: userdata geometry is UNMEASURED (first_lba=0). Read-only bring-up only; do not build write-capable payloads.")

if errors:
    print("FAIL:")
    for e in errors:
        print(" -", e)
    sys.exit(1)
print("check-pudding: OK (hardware invariants hold)")
