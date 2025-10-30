import asyncio
import dataclasses

import serial

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Button, RichLog, Header, Label

from dotbot_utils.hdlc import HDLCState, HDLCHandler

from dotbot_lh2_calibration.lighthouse2 import LighthouseManager, LH2Location


@dataclasses.dataclass
class CalibrationButton:
    """Calibration button dataclass."""

    button: Button
    value: int = -1
    data_set: bool = False


BUTTONS = {
    "top_left": CalibrationButton(
        button=Button("Top left", id="top_left", classes="point-btn"),
        value=0
    ),
    "top_right": CalibrationButton(
        button=Button("Top right", id="top_right", classes="point-btn"),
        value=1
    ),
    "bottom_left": CalibrationButton(
        button=Button("Bottom left", id="bottom_left", classes="point-btn"),
        value=2
    ),
    "bottom_right": CalibrationButton(
        button=Button("Bottom right", id="bottom_right", classes="point-btn"),
        value=3
    ),
}


class CalibrationApp(App):
    """Calibration application."""

    CSS_PATH = "calibration_app.tcss"

    def __init__(self, port, baudrate):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.serial = serial.Serial(self.port, self.baudrate, timeout=0.1)
        self.serial.flushInput()
        self.hdlc_handler = HDLCHandler()
        self.lh2_manager = LighthouseManager()
        self.text_log = None
        self.save_calibration_button = None

    def compose(self) -> ComposeResult:
        """Compose the UI."""
        yield Header(show_clock=True)
        self.main_container = Container()
        with self.main_container:
            with Container(id="calibration-controls"):
                with Container(id="calibration-point-controls"):
                    yield Label("Place the robot on calibration points and press the corresponding buttons:")
                    with Horizontal(id="point-buttons-top"):
                        yield BUTTONS["top_left"].button
                        yield BUTTONS["top_right"].button
                    with Horizontal(id="point-buttons-bottom"):
                        yield BUTTONS["bottom_left"].button
                        yield BUTTONS["bottom_right"].button
                with Container(id="calibration-logs"):
                    self.text_log = RichLog(id="log", highlight=True, markup=True)
                    yield self.text_log
            with Horizontal():
                self.save_calibration_button = Button("Save calibration", id="save-btn", variant="primary")
                yield self.save_calibration_button
                yield Button("Reset calibration", id="reset-btn", variant="warning")
                yield Button("Exit", id="exit-btn", variant="error")

    async def on_button_pressed(self, event: Button.Pressed):
        """Handle button presses."""
        btn_id = event.button.id
        if btn_id == "save-btn":
            self.save_calibration()
            return

        if btn_id == "reset-btn":
            self.reset_calibration()
            return

        if btn_id == "exit-btn":
            await self.action_quit()
            return

        if btn_id in BUTTONS:
            self.add_calibration_point(btn_id)

    async def on_mount(self):
        """Initialize the serial connection."""
        self.save_calibration_button.disabled = True
        self.text_log.write(f"[green]Connected to {self.port} @ {self.baudrate} baud[/]")
        self.read_task = asyncio.create_task(self.read_serial())
        self.lh2_manager.text_log = self.text_log

    def handle_received_payload(self, payload: bytes):
        """Handle a received frame."""
        if len(payload) != 16:
            self.text_log.write(f"[red]Invalid payload received '{payload.hex()}'[/]")
            return
        self.text_log.write(f"[cyan]Data received: {payload.hex()}[/]")
        location: LH2Location = LH2Location(
            count1=int.from_bytes(payload[0:4], byteorder="little", signed=False),
            polynomial_index1=int.from_bytes(payload[4:8], byteorder="little", signed=False),
            count2=int.from_bytes(payload[8:12], byteorder="little", signed=False),
            polynomial_index2=int.from_bytes(payload[12:16], byteorder="little", signed=False),
        )
        self.lh2_manager.last_location = location

    def on_byte_received(self, byte: bytes):
        """Handle a received byte from serial."""
        self.hdlc_handler.handle_byte(byte)
        if self.hdlc_handler.state == HDLCState.READY:
            try:
                data = self.hdlc_handler.payload
            except Exception as _:
                return
            self.handle_received_payload(data)

    async def read_serial(self):
        """Read bytes from serial port."""
        while self.serial and self.serial.is_open:
            try:
                byte = await asyncio.to_thread(self.serial.read, 1)
                if byte:
                    self.on_byte_received(byte)
            except Exception as e:
                self.text_log.write, f"[red]Error reading serial port : {e}[/]"
                break
        await self.action_quit()

    def add_calibration_point(self, point_id: str):
        """Add a calibration point."""
        if self.lh2_manager.add_calibration_point(BUTTONS[point_id].value) is False:
            self.text_log.write(f"[red]Error: No LH2 counts available. Cannot add calibration point.[/]")
            return
        BUTTONS[point_id].button.variant = "success"
        BUTTONS[point_id].data_set = True
        self.text_log.write(f"[cyan]Calibration point {BUTTONS[point_id].value} added.[/]")
        if all(button.data_set for button in BUTTONS.values()):
            self.save_calibration_button.disabled = False

    def reset_calibration(self):
        """Reset calibration data."""
        for button in BUTTONS.values():
            button.button.variant = "default"
            button.data_set = False
        self.save_calibration_button.disabled = True
        self.text_log.write("[green]Calibration data reset.[/]")

    def save_calibration(self):
        """Save calibration data to file."""
        try:
            self.lh2_manager.compute_calibration()
        except Exception as e:
            self.text_log.write(f"[red]Error computing calibration: {e}[/]")
            return
        self.text_log.write("[green]Calibration data saved.[/]")

    async def on_unmount(self):
        """Cleanup on app exit."""
        if self.serial and self.serial.is_open:
            await asyncio.to_thread(self.serial.close)
            self.serial = None
