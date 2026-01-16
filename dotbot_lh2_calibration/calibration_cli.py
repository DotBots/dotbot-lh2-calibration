"""CLI for DotBot LH2 calibration tools."""

# SPDX-FileCopyrightText: 2022-present Inria
# SPDX-FileCopyrightText: 2022-present Alexandre Abadie <alexandre.abadie@inria.fr>
#
# SPDX-License-Identifier: BSD-3-Clause

#!/usr/bin/env python3

import logging
import sys

import click
import serial
import structlog
from serial.tools import list_ports

from dotbot_lh2_calibration.calibration_app import CalibrationApp


def get_default_port():
    """Return default serial port."""
    ports = [port for port in list_ports.comports()]
    if sys.platform != "win32":
        ports = sorted([port for port in ports])
    if not ports:
        return "/dev/ttyACM0"
    return ports[0].device


SERIAL_PORT_DEFAULT = get_default_port()
SERIAL_BAUDRATE_DEFAULT = 115200
LH_NUM_DEFAULT = 0


@click.command()
@click.option(
    "-p",
    "--port",
    type=str,
    default=SERIAL_PORT_DEFAULT,
    help=f"Serial port used by 'serial' and 'edge' adapters. Defaults to '{SERIAL_PORT_DEFAULT}'",
)
@click.option(
    "-b",
    "--baudrate",
    type=int,
    default=SERIAL_BAUDRATE_DEFAULT,
    help=f"Serial baudrate used by 'serial' and 'edge' adapters. Defaults to {SERIAL_BAUDRATE_DEFAULT}",
)
@click.option(
    "-n",
    "--extra-lh-num",
    default=LH_NUM_DEFAULT,
    type=click.IntRange(min=0, max=5),
    help="Extra lighthouse number to calibrate.",
)
def main(port, baudrate, extra_lh_num):  # pylint: disable=redefined-builtin
    """Lighthouse calibration application."""

    # Configure structlog to suppress logs below CRITICAL level
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(logging.CRITICAL),
    )

    try:
        CalibrationApp(port, baudrate, extra_lh_num).run()
    except serial.serialutil.SerialException as exc:
        sys.exit(exc)
    except (SystemExit, KeyboardInterrupt):
        sys.exit(0)


if __name__ == "__main__":
    main()  # pragma: nocover, pylint: disable=no-value-for-parameter
