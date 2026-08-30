# WF3000A ImmortalWrt 6.6 云编译工程

本工程使用 [`padavanonly/immortalwrt-mt798x-6.6`](https://github.com/padavanonly/immortalwrt-mt798x-6.6) 的 `openwrt-24.10-6.6` 分支，通过 GitHub Actions 编译 KST-WF3000A 固件。

上游 6.6 分支目前没有 WF3000A 设备定义。本工程把旧版 WF3000A 板级描述移植到 `mediatek/filogic` 目标，并固定源码提交，避免上游变化导致补丁静默错位。

## 分区布局

内核 DTS 使用以下 NMBM 分区表：

```text
mtdparts=nmbm0:1024k(bl2),512k(u-boot-env),2048k(factory),2048k(fip),248320k(ubi)
```

对应十六进制布局：

| 分区 | 起始 | 大小 |
|---|---:|---:|
| bl2 | `0x0000000` | `0x0100000` |
| u-boot-env | `0x0100000` | `0x0080000` |
| factory | `0x0180000` | `0x0200000` |
| fip | `0x0380000` | `0x0200000` |
| ubi | `0x0580000` | `0x0f280000`（248320 KiB） |

总地址空间为 `0x0f800000`，即 NMBM 暴露的 248 MiB。DTS 中 `factory`、BL2 和 FIP 标记为只读。

## 固件内软件

- PassWall（Xray 后端）
- DDNS-GO
- AdGuard Home（LuCI 和核心二进制）
- Tailscale
- Argon 主题及配置页面
- LuCI Attended Sysupgrade 页面；系统自身的 `/sbin/sysupgrade` 也保留
- vnStat2 及 LuCI 页面
- WOL
- UPnP
- opkg 及 LuCI 软件包管理器
- nlbwmon 及 LuCI 流量统计页面

### 关于 ntopng

`ntopng` 没有出现在该源码对应的 ImmortalWrt 24.10 packages/LuCI feeds 中，也没有可直接用于此目标的维护中 OpenWrt 包。把 `CONFIG_PACKAGE_ntopng=y` 写进配置会被 `make defconfig` 直接移除，因此本工程没有伪造这个选项，而是使用官方支持的 `luci-app-nlbwmon` 作为按主机流量统计替代。vnStat2 同时保留，用于接口历史流量。

## 使用方法

1. 新建一个 GitHub 仓库，把本目录的**全部文件和隐藏的 `.github` 目录**上传到仓库根目录。
2. 打开仓库的 **Actions** 页面，选择 **Build WF3000A ImmortalWrt 6.6**。
3. 点击 **Run workflow**。
4. 默认只生成 Artifact。如果希望同时创建 Release，把 `publish_release` 设为 `true`。
5. 编译完成后下载 `WF3000A-ImmortalWrt-6.6-*` Artifact。

工作流会在编译前检查设备选项、所有要求的软件包选项和 UBI 分区大小。任何选项被 feeds 丢弃时，任务会立即失败，而不是生成缺包固件。

## 重要刷机说明

这是从旧内核板级定义移植到 Linux 6.6 的自定义设备支持，尚未在你的具体硬件上实机验证。请先准备串口和可用的 BL2/FIP 恢复方式。

- 先备份完整 NAND、Factory/EEPROM 和 U-Boot 环境。
- 确认机器确实是 256 MiB NAND、256 MiB RAM 的 WF3000A，并且交换机、LED GPIO 与该 DTS 一致。
- DTS 只定义 Linux 看到的分区，不会自动改写 U-Boot 环境。刷写前必须确认 U-Boot 的 `mtdparts` 与上面的布局一致。
- 不要在仍使用旧小 UBI 分区的系统上直接保留配置跨布局升级。
- 初次测试优先从 initramfs/恢复环境启动，再检查 `/proc/mtd`、NMBM、网口、Wi-Fi 校准和升级流程。
- Attended Sysupgrade 公共服务器通常不认识这个自定义设备；安装该页面不等于能够从公共 ASU 服务生成升级镜像。

本工程不会自动执行 `fw_setenv`，因为在未确认 `/etc/fw_env.config` 和当前引导器布局时修改 U-Boot 环境可能导致设备无法启动。

## 工程结构

```text
.github/workflows/build.yml       GitHub Actions 工作流
config/wf3000a.config             差异化固件配置
custom/wf3000a/                   Linux 6.6 DTS 和镜像定义
files/                            固件文件覆盖
scripts/prepare-source.py         安装设备支持并校验分区
scripts/prepare-packages.sh       拉取固定版本的 PassWall/AdGuardHome
feeds.conf.default                ImmortalWrt 24.10 feeds
```

## 固定版本

- ImmortalWrt 源码：`ec9ef10efc65da1e6d1de4e2c043c0e13d08eed8`
- PassWall：`2e5e6b9a5cc283098764da82ffe8b528b32f050d`
- PassWall packages：`ca9248d3f7c21f55b3519191ca0b85abbfc50136`
- small-package（仅 AdGuardHome 两个目录）：`c6ffb032320ad6758dc1f4d3deb61f746ffbc11d`

更新其中任何提交后，应重新检查 DTS、源码改写位置和软件包依赖。
