#!/usr/bin/env python3
"""Install the WF3000A Linux 6.6 board port into the pinned source tree."""

from pathlib import Path
import re
import shutil
import sys


def replace_once(path: Path, pattern: str, replacement: str) -> None:
    text = path.read_text(encoding="utf-8")
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise RuntimeError(f"expected exactly one patch location in {path}, got {count}")
    path.write_text(updated, encoding="utf-8", newline="\n")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: prepare-source.py OPENWRT_SOURCE_DIR")

    source = Path(sys.argv[1]).resolve()
    project = Path(__file__).resolve().parents[1]
    custom = project / "custom" / "wf3000a"

    dts_target = source / "target/linux/mediatek/dts/mt7981b-kst-wf3000a.dts"
    image_makefile = source / "target/linux/mediatek/image/filogic.mk"
    network_file = source / "target/linux/mediatek/filogic/base-files/etc/board.d/02_network"
    upgrade_file = source / "target/linux/mediatek/filogic/base-files/lib/upgrade/platform.sh"

    for required in (image_makefile, network_file, upgrade_file):
        if not required.is_file():
            raise FileNotFoundError(required)

    shutil.copyfile(custom / dts_target.name, dts_target)

    image_text = image_makefile.read_text(encoding="utf-8")
    if "define Device/kst_wf3000a" in image_text:
        raise RuntimeError("upstream already contains kst_wf3000a; review the port before building")
    fragment = (custom / "device.mk").read_text(encoding="utf-8")
    image_makefile.write_text(image_text.rstrip() + "\n" + fragment, encoding="utf-8", newline="\n")

    # Put this board in the same 3-LAN + 1-WAN DSA group as the Qihoo 360T7.
    replace_once(
        network_file,
        r"^(\s*)qihoo,360t7\|\\$",
        r"\1kst,wf3000a|\\\n\1qihoo,360t7|\\",
    )

    # Preserve the vendor MAC allocation used by the older WF3000A target.
    replace_once(
        network_file,
        r"^(\s*)qihoo,360t7\)$",
        r'''\1kst,wf3000a)
\1\tif [ -n "$(mtd_get_mac_ascii u-boot-env mac)" ]; then
\1\t\tlan_mac=$(mtd_get_mac_ascii u-boot-env mac)
\1\t\twan_mac=$(macaddr_add "$lan_mac" 2)
\1\t\tlabel_mac=$lan_mac
\1\telse
\1\t\twifi_mac=$(mtd_get_mac_binary factory 0x4)
\1\t\tlan_mac=$(macaddr_add "$wifi_mac" -1)
\1\t\twan_mac=$(macaddr_add "$wifi_mac" 1)
\1\t\tlabel_mac=$lan_mac
\1\tfi
\1\t;;
\1qihoo,360t7)''',
    )

    # The firmware uses kernel/rootfs UBI volumes and the normal NAND upgrader.
    replace_once(
        upgrade_file,
        r"^(\s*)qihoo,360t7\)$",
        r"\1kst,wf3000a|\\\n\1qihoo,360t7)",
    )

    # Requested table ends at 0x0f800000 (248 MiB NMBM address space).
    parts_kib = (1024, 512, 2048, 2048, 248320)
    assert sum(parts_kib) * 1024 == 0x0F800000
    print("WF3000A board port installed")
    print("mtdparts=nmbm0:1024k(bl2),512k(u-boot-env),2048k(factory),2048k(fip),248320k(ubi)")


if __name__ == "__main__":
    main()
