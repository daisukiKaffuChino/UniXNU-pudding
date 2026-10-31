# UniXNU pudding

[English](README.md) | 简体中文

小米 17（代号 `pudding`，p11u 系列）的设备支持，SoC 为高通 SM8850（第五代骁龙 8
至尊版）。设备配置选择
[UniXNU-sm8850-common](https://github.com/UniXNU/UniXNU-sm8850-common) 和
[UniXNU](https://github.com/UniXNU/UniXNU) 中的 `ipados-17.7.11-21H461` OS profile。

> **状态：研究与 bring-up 阶段。** 目前尚无任何 SM8850 设备启动过 UniXNU。板级参数
> 来自一台运行 Android 17（OS4.0.0.32.XPCCNXM）的零售小米 17，但尚未完成端到端
> 验证。本仓库记录的是进行中的工作，不是可用的移植。

仓库结构参考 [UniXNU-sheng](https://github.com/UniXNU/UniXNU-sheng) 与
[UniXNU-sm8550-common](https://github.com/UniXNU/UniXNU-sm8550-common)。

## 设备

| 项目 | 值 |
| --- | --- |
| 设备 | 小米 17，代号 `pudding`，p11u 系列 |
| SoC | 高通 SM8850，八核 Oryon |
| 内存 | 16 GB（实测 `MemTotal` 15,447,504 kB） |
| 屏幕 | 1220x2656，DSC command mode，60/90/120 Hz |
| 存储 | UFS |
| 触摸 | 多供应商（FocalTech / Synaptics / Novatek）；实测机器为 QUP4 SE0 SPI 上的 Synaptics TCM |
| GPU | Adreno 840v2，chip ID `0x44050a01` |
| OS profile | `ipados-17.7.11-21H461` |

## 仓库结构

| 路径 | 内容 |
| --- | --- |
| `board.toml` | 设备配置与组件选择 |
| `porting.toml` | 各子系统的输入、发现、证据与完成标准 |
| `feeds.toml` | 固定版本的 SoC 源 |
| `configs/pudding_defconfig` | 设备内核配置 |
| `dts/pudding.dts` | 内存、CPU 选择与外设配置 |
| `patches/xnu/series` | 板级补丁 |
| `proprietary-files.txt` | 固件输入路径 |
| `package/` | 设备策略、显示、输入与诊断 |
| `scripts/check-pudding.py` | 固件预检（板级不变量） |
| `unixnu.lock` | 已解析的源码版本 |
| `AGENTS.md` | 维护者与 agent 指引 |
| `local.toml.example` | 本地路径覆盖模板 |

## 当前状态

- 已选组件：`ArmDTPlatform`、`ArmCpu`、`SoftwareAES`、`XnuPrelink`、
  `DarwinBoot`、`VerifiedRoot`、`GopFramebuffer`、`AppleKeyStoreState`。
- 内核：`pudding_defconfig` 启用 CoreCrypto 14、pthread、ARM DT platform 与
  ARMCPU，crypto 使用 prelinked bootstrap。`NATIVE_UFS` 与 `NATIVE_ADRENO`
  在存储、GPU 阶段落地前保持关闭。
- 设备树：`0x8c00000000` 处 5 GiB 内存窗口、`0xfc800000` 的 splash 保留区、
  全部八核与 UFS。GPU、触摸与按键仍被注释，留待后续阶段。
- Payload：64 MiB 的 `PUDDINGESP` 卷。ABL 会丢弃 boot ramdisk，因此该卷写入
  非活动 boot 槽，由 `PuddingUfsDxe` 读回。
- 固件：需要 pudding 的 UEFI fork，位于 `Platforms/Xiaomi/puddingPkg`
  （尚未发布）。
- `feeds.toml` 仍为 `REQUIRED_SOC_COMMIT`，且 `UniXNU-sm8850-common` 尚未发布，
  因此在两者完成前 `./unixnu fetch` 无法解析 SoC 源。
- `porting.toml` 中所有子系统均为 `planned`；仅 configuration、display、
  input、GPU 带有 findings。

## 硬件要点

- TLMM 基址为 `0x0f100000`；vendor DT 中的 `0x0f000000` 是错误的。
- GIC redistributor 基址为 `0x17080000`。
- UFS 的 `sdX` 编号会在不同启动间互换；请按 GPT label 匹配分区。
- 未开时钟读取 MDSS 寄存器会导致该模块复位。
- p11u dtbo 描述的是 1200x2608 屏幕；实测机器报告 1220x2656。

细节与证据见 [porting.toml](porting.toml)。

## 开发记录

每次子系统改动都要同步维护 [porting.toml](porting.toml)。它记录硬件、配置、
步骤、发现、证据与完成标准。设备发布后文档站会渲染这份记录。维护者与 agent
遵循[同一份指南](https://unixnu.com/porting/records)。必需的 `Porting record`
CI 检查会校验结构、组件覆盖，以及改动代码时是否更新了 findings 或 evidence。

## 构建

在 UniXNU checkout 中运行：

```sh
./unixnu defconfig pudding_defconfig --device ../UniXNU-pudding
./unixnu fetch --device ../UniXNU-pudding
./unixnu status --device ../UniXNU-pudding --json
./unixnu build kernel --device ../UniXNU-pudding --kernelcache /path/to/kernelcache
./unixnu build firmware --device ../UniXNU-pudding --uefi ../uefi-pudding
./unixnu build payload --device ../UniXNU-pudding --unique-chip-id "$UNIXNU_UNIQUE_CHIP_ID" \
  --data-ramdisk /path/to/data.dbr --trust-cache /path/to/trustcache
./unixnu bootimg --device ../UniXNU-pudding --uefi ../uefi-pudding --dtb /path/to/firmware.dtb
```

输出位于 `out/pudding/ipados-17.7.11-21H461/pudding/`。payload 步骤会编译硬件
DTS 并写出 `kernel.macho.adt`；boot image 通过 `--dtb` 取用固件的 FDT。

这些命令目前还无法完成：SoC commit 未固定，UEFI fork 尚不存在。固件必须嵌入
UniXNU、UniXNUDxe、DarwinBoot 以及共享的 `UniXNURamDiskDxe`，并带 DiskIoDxe 与
FAT 支持；参见
[固件集成](https://unixnu.com/porting/uefi-firmware#required-integration)。

## 文档

- [Porting](https://unixnu.com/porting/)
- [设备仓库规范](https://unixnu.com/porting/device-repository)
- [设备树规范](https://unixnu.com/porting/device-tree)
- [组件目录](https://unixnu.com/reference/components)
- [Migration](https://unixnu.com/porting/migration)
- [Building](https://unixnu.com/building)

构建结果，以及设备的 boot、storage、display、input、GPU 观察，请分别记录，并附上
源码版本与命令。

## 本地构建输入

把 `local.toml.example` 复制为 `local.toml`（已被 Git 忽略），可将整个类别指向本地
目录。在 UniXNU checkout 的 `unixnu.local.toml` 中保存设备路径与启动参数。参见
[配置参考](https://unixnu.com/reference/configuration#local-build-inputs)。随后使用
`./unixnu kernel`、`./unixnu firmware`、`./unixnu payload` 与 `./unixnu bootimg`。
修改参数后需要重新构建 payload 与 boot image。参见
[启动参数](https://unixnu.com/xnu/boot-arguments#apply-arguments) 与
[green-bar 诊断](https://unixnu.com/guide/debugging#green-bar)。

## 许可证

[BSD-2-Clause-Patent](LICENSE)。
