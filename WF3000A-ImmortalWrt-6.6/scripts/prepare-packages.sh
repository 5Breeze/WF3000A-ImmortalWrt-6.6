#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: prepare-packages.sh OPENWRT_SOURCE_DIR" >&2
  exit 2
fi

source_dir="$(cd "$1" && pwd -P)"
custom_dir="$source_dir/package/custom"
mkdir -p "$custom_dir"

checkout_commit() {
  local url="$1"
  local commit="$2"
  local destination="$3"

  git init -q "$destination"
  git -C "$destination" remote add origin "$url"
  git -C "$destination" fetch -q --depth=1 origin "$commit"
  git -C "$destination" checkout -q --detach FETCH_HEAD
  rm -rf "$destination/.git"
}

# Reproducible PassWall snapshots.
checkout_commit \
  https://github.com/Openwrt-Passwall/openwrt-passwall-packages.git \
  ca9248d3f7c21f55b3519191ca0b85abbfc50136 \
  "$custom_dir/passwall-packages"

checkout_commit \
  https://github.com/Openwrt-Passwall/openwrt-passwall.git \
  2e5e6b9a5cc283098764da82ffe8b528b32f050d \
  "$custom_dir/passwall-luci"

# Only take the two AdGuardHome packages, avoiding unrelated small-package overrides.
small_tmp=/tmp/wf3000a-small-package
rm -rf "$small_tmp"
git init -q "$small_tmp"
git -C "$small_tmp" remote add origin https://github.com/kenzok8/small-package.git
git -C "$small_tmp" config core.sparseCheckout true
printf '%s\n' '/adguardhome/' '/luci-app-adguardhome/' > "$small_tmp/.git/info/sparse-checkout"
git -C "$small_tmp" fetch -q --depth=1 origin c6ffb032320ad6758dc1f4d3deb61f746ffbc11d
git -C "$small_tmp" checkout -q --detach FETCH_HEAD
cp -a "$small_tmp/adguardhome" "$custom_dir/adguardhome"
cp -a "$small_tmp/luci-app-adguardhome" "$custom_dir/luci-app-adguardhome"
rm -rf "$small_tmp"

echo "Pinned PassWall and AdGuardHome packages installed"
