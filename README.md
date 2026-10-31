# UniXNU pudding

English | [简体中文](README.zh.md)

Device support for Xiaomi 17, codename `pudding` (p11u family), with Qualcomm
SM8850 (Snapdragon 8 Elite Gen 5). The device profile selects
[UniXNU-sm8850-common](https://github.com/UniXNU/UniXNU-sm8850-common) and the
`ipados-17.7.11-21H461` OS profile in [UniXNU](https://github.com/UniXNU/UniXNU).

> **Status: research and bring-up.** Board inputs were collected from a live
> Xiaomi 17 running Android 17 (OS4.0.0.32.XPCCNXM) but have not been validated
> end to end. This repository records work in progress, not a usable port.

The layout follows [UniXNU-sheng](https://github.com/UniXNU/UniXNU-sheng) and
[UniXNU-sm8550-common](https://github.com/UniXNU/UniXNU-sm8550-common).

## Device

| Item | Value |
| --- | --- |
| Device | Xiaomi 17, codename `pudding`, p11u family |
| SoC | Qualcomm SM8850, eight Oryon cores |
| Memory | 16 GB (live `MemTotal` 15,447,504 kB) |
| Display | 1220x2656, DSC command mode, 60/90/120 Hz |
| Storage | UFS |
| Touch | Multi-sourced (FocalTech / Synaptics / Novatek); the live unit enumerates Synaptics TCM on QUP4 SE0 SPI |
| GPU | Adreno 840v2, chip ID `0x44050a01` |
| OS profile | `ipados-17.7.11-21H461` |

## Structure

| Path | Contents |
| --- | --- |
| `board.toml` | Device configuration and component selection |
| `porting.toml` | Subsystem inputs, findings, evidence and completion criteria |
| `feeds.toml` | Pinned SoC source |
| `configs/pudding_defconfig` | Device kernel settings |
| `dts/pudding.dts` | Memory, CPU selection, and peripheral configuration |
| `patches/xnu/series` | Board patches |
| `proprietary-files.txt` | Firmware input paths |
| `package/` | Device policy, display, input, and diagnostics |
| `scripts/check-pudding.py` | Firmware preflight checks for board invariants |
| `unixnu.lock` | Resolved source revisions |
| `AGENTS.md` | Agent and maintainer instructions |
| `local.toml.example` | Local path overrides template |

## Current state

- Components selected: `ArmDTPlatform`, `ArmCpu`, `SoftwareAES`, `XnuPrelink`,
  `DarwinBoot`, `VerifiedRoot`, `GopFramebuffer`, `AppleKeyStoreState`.
- Kernel: `pudding_defconfig` enables CoreCrypto 14, pthread, the ARM DT
  platform and ARMCPU, with a prelinked crypto bootstrap. `NATIVE_UFS` and
  `NATIVE_ADRENO` stay disabled until the storage and GPU stages land.
- Device tree: a 5 GiB memory window at `0x8c00000000`, the splash reservation
  at `0xfc800000`, all eight CPUs and UFS. GPU, touch and buttons remain
  commented out for later stages.
- Payload: a 64 MiB `PUDDINGESP` volume. ABL drops the boot ramdisk, so the
  volume is written to the inactive boot slot and read back by `PuddingUfsDxe`.
- Firmware: expects a pudding UEFI fork at `Platforms/Xiaomi/puddingPkg`
  (not published yet).
- `feeds.toml` still carries `REQUIRED_SOC_COMMIT`, and
  `UniXNU-sm8850-common` is not published yet, so `./unixnu fetch` cannot
  resolve the SoC source until both are done.
- `porting.toml` marks every subsystem `planned`; only configuration, display,
  input and GPU carry findings.

## Hardware notes

- TLMM base is `0x0f100000`; the vendor DT value `0x0f000000` is wrong.
- GIC redistributor base is `0x17080000`.
- UFS `sdX` indices swap between boots; match partitions by GPT label.
- MDSS register reads without clocks reset the block.
- The p11u dtbo describes a 1200x2608 panel; the live unit reports 1220x2656.

Details and evidence live in [porting.toml](porting.toml).

## Development record

Maintain [porting.toml](porting.toml) with every subsystem change. It records
hardware, configuration, procedures, findings, evidence and completion criteria.
The documentation site renders it once the device is published. Maintainers and
agents follow the [same guide](https://unixnu.com/porting/records). The required
`Porting record` CI check validates structure, component coverage and updates to
findings or evidence for changed code.

## Build

Run these commands from the UniXNU checkout:

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

Outputs are under `out/pudding/ipados-17.7.11-21H461/pudding/`. The payload step
compiles the hardware DTS and writes `kernel.macho.adt`; the boot image takes the
firmware's FDT with `--dtb`.

These commands do not complete yet: the SoC commit is unpinned and the UEFI fork
does not exist. The firmware must embed UniXNU, UniXNUDxe, DarwinBoot and the
shared `UniXNURamDiskDxe` with DiskIoDxe and FAT support; follow
[firmware integration](https://unixnu.com/porting/uefi-firmware#required-integration).

## Documentation

- [Porting](https://unixnu.com/porting/)
- [Device repository specification](https://unixnu.com/porting/device-repository)
- [Device tree specification](https://unixnu.com/porting/device-tree)
- [Component catalog](https://unixnu.com/reference/components)
- [Migration](https://unixnu.com/porting/migration)
- [Building](https://unixnu.com/building)

Report build results and device boot, storage, display, input, and GPU
observations separately, with source revisions and commands.

## Local build inputs

Copy `local.toml.example` to `local.toml` (ignored by Git) to point whole
categories at local directories. Save device paths and boot arguments in
`unixnu.local.toml` in the UniXNU checkout. See the
[configuration reference](https://unixnu.com/reference/configuration#local-build-inputs).
Then use `./unixnu kernel`, `./unixnu firmware`, `./unixnu payload`, and
`./unixnu bootimg`. Argument changes require rebuilding the payload and boot
image. See [boot arguments](https://unixnu.com/xnu/boot-arguments#apply-arguments)
and [green-bar diagnosis](https://unixnu.com/guide/debugging#green-bar).

## License

[BSD-2-Clause-Patent](LICENSE).
