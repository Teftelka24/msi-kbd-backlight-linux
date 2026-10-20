#!/usr/bin/env python3
"""Keyboard backlight control for the MSI MysticLight MS-1563 (USB 1462:1563).

The packets are replayed byte for byte from MSI Center USB captures
(OpenRGB issue #2289, files *.pcapng next to this script).
Only the mode, brightness and colour fields change; all other bytes are kept as-is.

Usage (as root):
  kbd-backlight.py off
  kbd-backlight.py on [white|red|green|blue] [1-5]    # 5 = brightest
"""
import fcntl
import glob
import os
import sys

VID_PID = "0003:00001462:00001563"
HERE = os.path.dirname(os.path.realpath(__file__))

# Report ID 2, 64 bytes, as sent by MSI Center (Whole-Device-Off capture)
TEMPLATE = bytes.fromhex(
    "020000000a010000ffff5000ffff0000ff000000ff9600ffff00ff00"
    + "00" * 36
)
MODE_OFF, MODE_STEADY = 0x00, 0x01
LEVELS = {1: 0x02, 2: 0x04, 3: 0x06, 4: 0x08, 5: 0x0A}   # captured values
COLORS = {
    "white": (0xFF, 0xFF, 0xFF),
    "red": (0xFF, 0x00, 0x00),
    "green": (0x00, 0xFF, 0x00),
    "blue": (0x00, 0x00, 0xFF),
}


def hidiocsfeature(length):
    # _IOC(_IOC_READ|_IOC_WRITE, 'H', 0x06, len)
    return (3 << 30) | (length << 16) | (ord("H") << 8) | 0x06


def find_device():
    """Return /dev/hidrawN of the MS-1563 after checking its report descriptor."""
    expected = open(os.path.join(HERE, "1462_1563_ReportDescriptor.txt")).read()
    expected = bytes.fromhex("".join(expected.splitlines()[1:]))
    for dev in glob.glob("/sys/bus/hid/devices/*"):
        uevent = open(os.path.join(dev, "uevent")).read()
        if f"HID_ID={VID_PID}" not in uevent:
            continue
        if open(os.path.join(dev, "report_descriptor"), "rb").read() != expected:
            sys.exit(f"{dev}: report descriptor differs from the captured one, refusing")
        nodes = os.listdir(os.path.join(dev, "hidraw"))
        return "/dev/" + nodes[0]
    sys.exit("MysticLight 1462:1563 not found")


def build(mode, level=5, color="white"):
    pkt = bytearray(TEMPLATE)
    pkt[2] = mode
    if mode == MODE_STEADY:
        pkt[4] = LEVELS[level]
        pkt[6:9] = bytes(COLORS[color])
    return bytes(pkt)


def main(argv):
    if not argv or argv[0] not in ("off", "on"):
        sys.exit(__doc__)
    if argv[0] == "off":
        pkt = build(MODE_OFF)
    else:
        color = next((a for a in argv[1:] if a in COLORS), "white")
        level = next((int(a) for a in argv[1:] if a.isdigit()), 5)
        if level not in LEVELS:
            sys.exit("brightness must be 1-5")
        pkt = build(MODE_STEADY, level, color)

    path = find_device()
    if "--dry-run" in argv:
        print(path, pkt.hex())
        return
    with open(path, "rb+", buffering=0) as f:
        fcntl.ioctl(f, hidiocsfeature(len(pkt)), pkt)
    print("ok:", argv[0])


if __name__ == "__main__":
    main(sys.argv[1:])
