# SPDX-FileCopyrightText: 2022-present Inria
# SPDX-FileCopyrightText: 2022-present Alexandre Abadie <alexandre.abadie@inria.fr>
#
# SPDX-License-Identifier: BSD-3-Clause

#!/usr/bin/env python3

"""Main module of the Dotbot controller command line tool."""

import click

from dotbot import (
    SERIAL_BAUDRATE_DEFAULT,
    SERIAL_PORT_DEFAULT,
)


@click.command()
@click.option(
    "-p",
    "--port",
    type=str,
    default=SERIAL_PORT_DEFAULT,
    help=f"Serial port used to connect to the robot. Defaults to '{SERIAL_PORT_DEFAULT}'",
)
@click.option(
    "-b",
    "--baudrate",
    type=int,
    default=SERIAL_BAUDRATE_DEFAULT,
    help=f"Serial baudrate used to connect to the robot. Defaults to {SERIAL_BAUDRATE_DEFAULT}",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    default=False,
    help="Run in verbose mode (all payloads received are printed in terminal)",
)
def main(
    port, baudrate, verbose
):  # pylint: disable=redefined-builtin,too-many-arguments
    """LH2 Calibration Tool."""
    print(f"Welcome to the DotBots LH2 calibration tool.")


if __name__ == "__main__":
    main()  # pragma: nocover, pylint: disable=no-value-for-parameter
