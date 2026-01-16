import asyncio
import dataclasses

import serial
from dotbot_utils.hdlc import HDLCHandler, HDLCState
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import (
    Button,
    Header,
    Label,
    RichLog,
    Select,
    TabbedContent,
    TabPane,
    Tabs,
)

from dotbot_lh2_calibration.lighthouse2 import (
    LH2Counts,
    LH2CountsPair,
    LighthouseManager,
)

TEST_CALIBRATION_COUNTS = [
    LH2Counts(lh_index=0, count1=37511, count2=71499),
    LH2Counts(lh_index=0, count1=41045, count2=72179),
    LH2Counts(lh_index=0, count1=43645, count2=77050),
    LH2Counts(lh_index=0, count1=40027, count2=75524),
]


@dataclasses.dataclass
class CalibrationButton:
    """Calibration button dataclass."""

    button: Button
    value: int = -1
    data_set: bool = False


BUTTONS = {
    "top_left": CalibrationButton(
        button=Button("Top left", id="top_left", classes="point-btn"), value=0
    ),
    "top_right": CalibrationButton(
        button=Button("Top right", id="top_right", classes="point-btn"),
        value=1,
    ),
    "bottom_left": CalibrationButton(
        button=Button("Bottom left", id="bottom_left", classes="point-btn"),
        value=2,
    ),
    "bottom_right": CalibrationButton(
        button=Button("Bottom right", id="bottom_right", classes="point-btn"),
        value=3,
    ),
}

EXTRA_LH_BUTTONS = {
    "lh1": CalibrationButton(
        button=Button("Add point", id="lh1", classes="lh-btn", disabled=True),
        value=1,
    ),
    "lh2": CalibrationButton(
        button=Button("Add point", id="lh2", classes="lh-btn", disabled=True),
        value=2,
    ),
    "lh3": CalibrationButton(
        button=Button("Add point", id="lh3", classes="lh-btn", disabled=True),
        value=3,
    ),
    "lh4": CalibrationButton(
        button=Button("Add point", id="lh3", classes="lh-btn", disabled=True),
        value=3,
    ),
    "lh5": CalibrationButton(
        button=Button("Add point", id="lh3", classes="lh-btn", disabled=True),
        value=3,
    ),
}


class CalibrationApp(App):
    """Calibration application."""

    CSS_PATH = "calibration_app.tcss"

    def __init__(self, port, baudrate, extra_lh_num):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.extra_lh_num = extra_lh_num
        self.serial = serial.Serial(self.port, self.baudrate, timeout=0.1)
        self.serial.flushInput()
        self.hdlc_handler = HDLCHandler()
        self.lh2_manager = LighthouseManager(extra_lh_num=self.extra_lh_num)
        self.data_log = None
        self.app_log = None
        self.save_calibration_button = None
        self.last_counts: list[LH2Counts | None] = [None, None, None, None]
        self.calibration_counts: list[LH2Counts] = [None] * (
            len(EXTRA_LH_BUTTONS) + 1
        )
        self.extra_lh_counts_pairs: list[list[LH2CountsPair]] = [
            [] for _ in range(len(EXTRA_LH_BUTTONS))
        ]
        self.extra_lh_logs = []
        self.extra_lh_index_references = [0] * self.extra_lh_num

    def compose(self) -> ComposeResult:
        """Compose the UI."""
        yield Header(show_clock=True)
        self.main_container = Container(id="main-container")
        with self.main_container:
            with Container(classes="calibration-controls"):
                with Container(classes="calibration-point-controls"):
                    with Horizontal(classes="calibration-label"):
                        yield Label("Reference calibration points (LH0):")
                    with Horizontal(classes="calibration-point-button-group"):
                        yield BUTTONS["top_left"].button
                        yield BUTTONS["top_right"].button
                    with Horizontal(classes="calibration-point-button-group"):
                        yield BUTTONS["bottom_left"].button
                        yield BUTTONS["bottom_right"].button
                with Container(id="data-logs"):
                    self.data_log = RichLog(
                        id="log", highlight=True, markup=True
                    )
                    yield self.data_log
            if self.extra_lh_num > 0:
                with TabbedContent(id="extra-lh-tabs", initial="tab-lh1"):
                    for lh in range(self.extra_lh_num):
                        with TabPane(
                            f"LH{lh + 1} calibration", id=f"tab-lh{lh+1}"
                        ):
                            with Container(
                                classes="extra-lh-calibration-section"
                            ):
                                with Container(
                                    classes="calibration-extra-lh-container"
                                ):
                                    with Horizontal(
                                        classes="calibration-extra-lh-point-controls"
                                    ):
                                        yield Select(
                                            classes="lh-reference-select",
                                            id=f"lh{lh + 1}_reference",
                                            options=[
                                                (
                                                    f"Reference: LH{index}",
                                                    index,
                                                )
                                                for index in range(
                                                    0, self.extra_lh_num + 1
                                                )
                                                if index != lh + 1
                                            ],
                                            value=0,
                                        )
                                        yield EXTRA_LH_BUTTONS[
                                            f"lh{lh+1}"
                                        ].button
                                with Container(
                                    classes="calibration-state-info"
                                ):
                                    log = RichLog(
                                        id=f"extra_lh_logs_{lh + 1}",
                                        highlight=True,
                                        markup=True,
                                    )
                                    self.extra_lh_logs.append(log)
                                    yield log
            with Container(id="app-logs"):
                self.app_log = RichLog(
                    id="app_log", highlight=True, markup=True
                )
                yield self.app_log
            with Horizontal():
                self.save_calibration_button = Button(
                    "Save calibration", id="save-btn", variant="primary"
                )
                yield self.save_calibration_button
                yield Button(
                    "Reset calibration", id="reset-btn", variant="warning"
                )
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
            self.add_initial_calibration_point(btn_id)

        if btn_id in EXTRA_LH_BUTTONS:
            self.add_extra_lh_point(btn_id)

    async def on_select_changed(self, event: Select.Changed):
        """Handle select changes."""
        select_id = event.select.id
        lh_index = int(select_id[2:3])
        self.extra_lh_index_references[lh_index - 1] = event.value

    async def on_mount(self):
        """Initialize the serial connection."""
        self.save_calibration_button.disabled = True
        self.data_log.write(
            f"[green]Connected to {self.port} @ {self.baudrate} baud[/]"
        )

        self.read_task = asyncio.create_task(self.read_serial())
        self.lh2_manager.text_log = self.data_log

        # debug
        # with open("/tmp/debug_counts.txt", "w") as debug_file:
        #     debug_file.write("----- New Session -----\n")

    def handle_received_payload(self, payload: bytes):
        """Handle a received frame."""
        if len(payload) != 9:
            self.data_log.write(
                f"[red]Invalid payload received '{payload.hex()}'[/]"
            )
            return

        counts: LH2Counts = LH2Counts(
            lh_index=int.from_bytes(
                payload[0:1], byteorder="little", signed=False
            ),
            count1=int.from_bytes(
                payload[1:5], byteorder="little", signed=False
            ),
            count2=int.from_bytes(
                payload[5:9], byteorder="little", signed=False
            ),
        )
        self.data_log.write(f"[cyan]Counts received: {counts}[/]")
        self.last_counts[counts.lh_index] = counts

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
                self.data_log.write, f"[red]Error reading serial port : {e}[/]"
                break
        await self.action_quit()

    def add_initial_calibration_point(self, point_id: str):
        """Add a calibration point."""
        # debug
        # self.last_counts[0] = TEST_CALIBRATION_COUNTS[BUTTONS[point_id].value]

        if self.last_counts[0] is None:
            self.app_log.write(
                "[red]Error: No LH2 counts available. Cannot add calibration point.[/]"
            )
            return

        counts = self.last_counts[0]
        self.last_counts[0] = None
        self.calibration_counts[BUTTONS[point_id].value] = counts

        # debug
        # with open("/tmp/debug_counts.txt", "a") as debug_file:
        #     debug_file.write(
        #         f"LH0, point {BUTTONS[point_id].value}: {counts}\n"
        #     )

        BUTTONS[point_id].button.variant = "success"
        BUTTONS[point_id].data_set = True
        self.app_log.write(
            f"[cyan]Calibration point {BUTTONS[point_id].value} added ({counts.count1}, {counts.count2}).[/]"
        )
        if all(button.data_set for button in BUTTONS.values()):
            if self.extra_lh_num > 0:
                self.app_log.write(
                    "[yellow]All initial calibration points set.\n"
                    "Proceed to extra lighthouse calibration.[/]"
                )
                EXTRA_LH_BUTTONS["lh1"].button.disabled = False
            else:
                self.app_log.write(
                    "[green]All calibration points set.\n"
                    "Ready to save calibration.[/]"
                )
                self.save_calibration_button.disabled = False

    def add_extra_lh_point(self, lh_id: str):
        """Add a shared calibration point."""
        lh_index = EXTRA_LH_BUTTONS[lh_id].value
        ref_index = self.extra_lh_index_references[lh_index - 1]

        # debug
        # self.last_counts[ref_index] = LH2Counts(ref_index, 49341, 85887)

        # Get reference counts from LH0
        ref_counts = self.last_counts[ref_index]
        if ref_counts is None:
            self.app_log.write(
                "[red]Error: No reference LH0 counts available. Cannot add calibration point.[/]"
            )
            return

        # debug
        # self.last_counts[lh_index] = LH2Counts(lh_index, 49341, 85887)

        # Get counts from extra lighthouse
        new_counts = self.last_counts[lh_index]
        self.last_counts[lh_index] = None
        if new_counts is None:
            self.app_log.write(
                f"[red]Error: No new LH{lh_index} counts available. Cannot add calibration point.[/]"
            )
            return

        # Create counts are mathching expected lighthouse
        if lh_index != new_counts.lh_index:
            self.app_log.write(
                f"[red]Error: Received counts polynomial index {new_counts.lh_index} does not match expected LH{lh_index}.[/]"
            )
            return

        counts_pair = LH2CountsPair(
            ref_index=ref_index, ref_counts=ref_counts, new_counts=new_counts
        )
        self.extra_lh_counts_pairs[lh_index - 1].append(counts_pair)

        # debug
        # with open("/tmp/debug_counts.txt", "a") as debug_file:
        #     debug_file.write(
        #         f"LH{EXTRA_LH_BUTTONS[lh_id].value}: {counts_pair}\n"
        #     )

        calibration_count_len = len(self.extra_lh_counts_pairs[lh_index - 1])
        self.extra_lh_logs[lh_index - 1].write(
            f"[cyan]Calibration point added for LH{lh_index} (count: {calibration_count_len}).[/]"
        )
        if calibration_count_len >= 4:
            EXTRA_LH_BUTTONS[lh_id].button.variant = "success"
            EXTRA_LH_BUTTONS[lh_id].data_set = True
            next_lh_index = lh_index + 1
            if next_lh_index <= self.extra_lh_num:
                next_btn_id = f"lh{next_lh_index}"
                EXTRA_LH_BUTTONS[next_btn_id].button.disabled = False
        if all(
            button.data_set
            for button in list(EXTRA_LH_BUTTONS.values())[: self.extra_lh_num]
        ):
            self.app_log.write(
                "[green]All extra calibration points set.\n"
                "Ready to save calibration.[/]"
            )
            self.save_calibration_button.disabled = False

    def reset_calibration(self):
        """Reset calibration data."""
        for button in BUTTONS.values():
            button.button.variant = "default"
            button.data_set = False
        for button in EXTRA_LH_BUTTONS.values():
            button.data_set = False
            button.button.variant = "default"
            button.button.disabled = True
        self.calibration_counts = [None] * 4
        self.extra_lh_counts_pairs = [[], [], []]
        self.save_calibration_button.disabled = True
        self.app_log.write("[green]Calibration data reset.[/]")

    def save_calibration(self):
        """Save calibration data to file."""
        try:
            self.lh2_manager.compute_calibration(
                self.calibration_counts, self.extra_lh_counts_pairs
            )
        except Exception as e:
            self.app_log.write(f"[red]Error computing calibration: {e}[/]")
            return
        try:
            # debug
            with open("/tmp/debug_calibration.txt", "w") as debug_file:
                for index, homography in enumerate(
                    self.lh2_manager.homographies
                ):
                    debug_file.write(
                        f"Homography LH{index}:\n{homography.matrix}\n"
                    )
            self.lh2_manager.save_calibration()
        except Exception as e:
            self.app_log.write(f"[red]Error saving calibration: {e}[/]")
            return

        self.app_log.write("[green]Calibration data saved.[/]")

    async def on_unmount(self):
        """Cleanup on app exit."""
        if self.serial and self.serial.is_open:
            await asyncio.to_thread(self.serial.close)
            self.serial = None
