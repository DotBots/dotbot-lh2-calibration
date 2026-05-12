# dotbot-lh2-calibration

Utilities for Lighthouse v2 calibration in the DotBot ecosystem.

## Description

`dotbot-lh2-calibration` offers tools and methods to calibrate Lighthouse v2
base stations (LH2) relative to the DotBot robots.

## Installation

You can install the package from PyPI:

```bash
pip install dotbot-lh2-calibration
```

## Getting the Code

Clone the repository using Git:

```
git clone https://github.com/DotBots/dotbot-lh2-calibration.git
```

## Usage

### Build the calibration firmware

The source code of calibration firmware is available in the
[calibration](calibration) directory and can be built using
[SEGGER Embedded Studio for ARM](https://www.segger.com/downloads/embedded-studio).

In SEGGER embedded studio, use the package manager
(available in menu Tools > Package manager) to install the CMSIS 5 CMSIS-CORE,
CMSIS-DSP and nRF packages.

For details on SEGGER Embedded Studio, read the
[online documentation](https://studio.segger.com/index.htm?https://studio.segger.com/home.htm).

Flash the firmware on the robot.

### Calibration script

The calibration script is a Terminal User Interface application that connects
to the serial port (at 115200 bauds) of the robot to collect the Lighthouse
raw data.

Run the script as follows:

```
dotbot-calibration
```

Useful options at a glance:

| Flag | Default | Meaning |
|---|---|---|
| `-p`, `--port` | platform default | Serial port the calibration firmware is exposed on (e.g. `/dev/tty.usbmodem...` on macOS, `/dev/ttyACM0` on Linux). |
| `-b`, `--baudrate` | 115200 | Serial baudrate. |
| `-d`, `--distance` | `500` | **Side length, in millimeters**, of the physical square formed by the 4 calibration reference points. |
| `-n`, `--extra-lh-num` | `0` | Number of additional lighthouses beyond the first one (0–5). One homography per lighthouse is computed. |
| `--output-data` | `~/.dotbot/calibration.out` | Where to save the raw calibration data. |
| `--input-data` | — | Re-process a previously saved calibration file instead of capturing live data. |

**Units gotcha**: `-d` is in **millimeters**. Common values:

- `-d 800` → 80 cm square → usable arena ≈ 4 m × 4 m. Used for the 700-DotBot
  deployment in Limerick (Jan 2026).
- `-d 500` (default) → 50 cm calibration square → usable arena ≈ 2.5 m × 2.5 m.
- `-d 400` → 40 cm square → usable arena ≈ 2.0 m × 2.0 m.
- `-d 100` → 10 cm square (small desk test) → arena ≈ 0.5 m × 0.5 m.

The usable arena is roughly **5× the calibration square side**, because the
reference points used internally (`REFERENCE_POINTS_DEFAULT` in
`lighthouse2.py`) occupy the central 20 % of the normalized plane and are
scaled by `distance * 5`.

Place the robot on the ground on the calibration points and in the UI, press
the corresponding buttons.
Once all 4 calibration points are checked, you can save the calibration.

The calibration file is stored in `~/.dotbot/calibration.out`.

### Exporting calibration to swarmit firmware

The `dotbot-calibration-exporter` subcommand converts the binary
`~/.dotbot/calibration.out` into a C header that the swarmit bootloader
compiles in. It takes a single argument: the **directory** in which to write
the generated `lh2_calibration.h` file (the file name itself is fixed).

```
dotbot-calibration-exporter <path-to-output-dir>
```

`--help`:

```
Usage: dotbot-calibration-exporter [OPTIONS] OUTPUT_PATH

  Export DotBot calibration data to a file.

Options:
  --help  Show this message and exit.
```

Example targeting a local checkout of swarmit:

```
dotbot-calibration-exporter $SWARMIT/device/bootloader/Source
```

This writes `$SWARMIT/device/bootloader/Source/lh2_calibration.h`, which the
bootloader includes to produce a build with the calibration baked in. Rebuild
and reflash the bootloader for the new calibration to take effect.

> **Note**: with PR [#127][pr-127] (remote LH2 calibration over Mari) the
> exporter is no longer required for already-flashed robots — the swarmit CLI
> can push `~/.dotbot/calibration.out` directly to running devices. The header
> path stays useful for first-time flashing of a fresh board.

[pr-127]: https://github.com/DotBots/swarmit/pull/127

## Calibration layout

```
 ←─────────────── 5·d ────────────→
┌──────────────────────────────────┐  ↑
│                                  │  │
│                                  │  │
│                                  │  │
│           ←─── d ───→            │  │
│       TL  ●─────────●  TR        │  │
│           │         │            │ 5·d
│           │         │            │  │
│           │         │            │  │
│       BL  ●─────────●  BR        │  │
│                                  │  │
│←── 2·d ──→                       │  │
│                                  │  │
└──────────────────────────────────┘  ↓

                             ⌖ LH2 base station
                               (mounted ~2 m up,
                                facing the arena)
```

Legend:

- **TL / TR / BL / BR**: top-left, top-right, bottom-left, bottom-right
  reference points (the 4 dots the robot is placed on, one at a time).
- **d**: side of the physical calibration square, set with `--distance` (mm).
- **5·d**: usable arena side. The calibration square sits centered, with a
  **2·d** margin on every side.
- **⌖ LH2 base station**: mounted ~2 m up, facing the arena.

Example: `-d 500` (default) → d = 500 mm = 50 cm → 5·d = 2.5 m arena
→ 2·d = 1 m margin on each side.

Procedure: place the robot on each dot (TL → TR → BL → BR), press the matching
button in the TUI, and save when all four are captured.
Output: `~/.dotbot/calibration.out`.

## License

This project is published under the terms of the BSD-3-Clause license.
