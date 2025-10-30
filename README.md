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

## Build the calibration firmware

The source code of calibration firmware is available in the
[calibration](calibration) directory and can be built using
[SEGGER Embedded Studio for ARM](https://www.segger.com/downloads/embedded-studio).

In SEGGER embedded studio, use the package manager
(available in menu Tools > Package manager) to install the CMSIS 5 CMSIS-CORE,
CMSIS-DSP and nRF packages.

For details on SEGGER Embedded Studio, read the
[online documentation](https://studio.segger.com/index.htm?https://studio.segger.com/home.htm).

## License

This project is published under the terms of the BSD-3-Clause license.
