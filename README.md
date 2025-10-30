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

# Build the calibration firmware

The source code of calibration firmware is available in the
[calibration](calibration) directory and can be built using
[SEGGER Embedded Studio for ARM](https://www.segger.com/downloads/embedded-studio).

In SEGGER embedded studio, use the package manager
(available in menu Tools > Package manager) to install the CMSIS 5 CMSIS-CORE,
CMSIS-DSP and nRF packages.

For details on SEGGER Embedded Studio, read the
[online documentation](https://studio.segger.com/index.htm?https://studio.segger.com/home.htm).

Flash the firmware on the robot.

# Calibration script

The calibration script is a Terminal User Interface application that connects
to the serial port (at 115200 bauds) of the robot to collect the Lighthouse
raw data.

Run the script as follows:

```
dotbot-calibration
```

Place the robot on the ground on the calibration points and in the UI, press
the corresponding buttons.
Once all 4 calibration points are checked, you can save the calibration.

The calibration file is stored in `~/.dotbot/calibration.out`.

## License

This project is published under the terms of the BSD-3-Clause license.
