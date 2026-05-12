# dotbot-lh2-calibration

## Purpose

Lighthouse v2 (LH2) calibration tooling for the DotBot ecosystem. Two pieces:

1. **Firmware**: nRF52/nRF5340 firmware (~90 LOC `main.c`) that streams raw LH2 sensor data over UART/HDLC.
2. **Python tool**: a Textual TUI (`dotbot-calibration`) that computes a homography from 4 reference points and writes `~/.dotbot/calibration.out`.

Implements the homography (single-LH planar with 4 known markers) and multi-LH paths from the Lighthouse RAL 2024 paper. The fundamental-matrix 3D path described in that paper is **not** implemented here; multi-LH at the scale of 6+ basestations is open work flagged in the 725-bot deployment review.

## Tech stack

- **Firmware**: C, nRF52/nRF5340; SEGGER Embedded Studio (`.emProject`) — no Make/CMake, no headless build
- **Python**: ≥3.7, `hatchling`, deps: `click`, `numpy`, `opencv-python`, `pydotbot-utils`, `textual`
- **Style/test**: `ruff`, `isort`, `black`, `pytest`
- **Package**: PyPI as `dotbot-lh2-calibration`; pip

## Submodules

This repo has **one** git submodule. After cloning, init it:

```bash
git clone --recurse-submodules git@github.com:DotBots/dotbot-lh2-calibration.git
# or, if already cloned:
git submodule update --init --recursive
```

| Submodule | Path | Pinned (snapshot 2026-05-12) |
|---|---|---|
| `DotBot-libs` | `dotbot-libs/` | `0.1.0-46-g1ebdd59` |

The firmware in `calibration/main.c` requires headers from `dotbot-libs/` (`board.h`, `lh2.h`, `hdlc.h`, `timer.h`, `uart.h`); the submodule must be checked out for the firmware build to resolve. Pins the same SHA as `DotBot-firmware`.

## Entry points

- `calibration/main.c` — the entire firmware (single ~90 LOC file streaming LH2 frames over HDLC)
- `dotbot_lh2_calibration/calibration_cli.py` — `dotbot-calibration` CLI; orchestrates the TUI
- `dotbot_lh2_calibration/lighthouse2.py` — math core (`LighthouseManager`, `calculate_camera_point`, homography)

## Build / run / test

```bash
# Firmware (no headless path)
# Open a .emProject in SEGGER Embedded Studio, install CMSIS 5 / CMSIS-DSP / nRF packages, build, flash.

# Python
pip install dotbot-lh2-calibration            # or `pip install -e .`
dotbot-calibration                             # TUI
dotbot-calibration-exporter

# Tests
pytest                                         # only tests/test_lighthouse2.py exists
```

**No CI** (`.github/` absent). **No headless firmware build** documented.

## Cross-repo dependencies

- **`DotBot-libs`** — git submodule at `dotbot-libs/` (`.gitmodules`). Required by firmware (`board.h`, `lh2.h`, `hdlc.h`, `timer.h`, `uart.h` in `calibration/main.c`).
- **`PyDotBot-utils`** — `pyproject.toml:23` (`pydotbot-utils >= 0.1.0`); imports `dotbot_utils.hdlc` in `calibration_app.py:6`
- No references to: `swarmit`, `mari`, `marilib`, `DotBot-firmware`, `PyDotBot`, `dotbot-provision`, `qrkey`
- **Downstream consumer**: `~/.dotbot/calibration.out` is consumed by `PyDotBot` (no schema/version yet — friction)

## State of repo (snapshot 2026-05-05)

- Last commit on `main`: 2026-04-29
- Total commits on `main`: 26
- Commits in last 90 days: 2
- Branches:
  - `multi-lighthouse` — last 2026-01-29, 0 ahead / 2 behind. **Already merged into main** (commits like "refactor to support multi lighthouse setup" exist on main); branch is a leftover, safe to delete.
- TODO/FIXME/XXX/HACK: 0

## Hot spots and known gaps

- **Multi-lighthouse work landed on main**; the `multi-lighthouse` branch is leftover. Current code implements the homography (2D, planar, 4 reference points) approach with multi-LH support up to `--extra-lh-num` cap of 5. Fundamental-matrix 3D and ≥6 basestations are open work.
- **No CI, no headless firmware build, no Makefile**. Seven sibling `.emProject` files at root (`dotbot-v1/v2/v3`, `nrf52833dk`, `nrf52840dk`, `nrf5340dk-app`, `calibration/calibration.emProject`) duplicate board configs.
- **Single test file** with hardcoded numeric expectations; `lighthouse2.py` (~11 KB, OpenCV homography) has no unit coverage of multi-LH paths.
- **`requires-python = ">=3.7"` while `numpy>=2.1` requires Python 3.10+** — version floor wrong.
- **`~/.dotbot/calibration.out` has no schema/versioning** — friction for downstream consumers (`PyDotBot`).

## Branch policy

- Default: `main`
- `multi-lighthouse` branch can be deleted (already merged).

## Agent-task ideas

- **Add GitHub Actions** for ruff + pytest (no CI today).
- **Bump `requires-python`** to match numpy floor (≥3.10).
- **Add headless firmware build** (CMake or reuse `DotBot-firmware` build infrastructure).
- **Expand pytest coverage** of `LighthouseManager` multi-LH paths.
- **Define a versioned JSON schema** for `~/.dotbot/calibration.out`; document it for `PyDotBot` consumers.
- **Delete merged `multi-lighthouse` branch.**
- **Implement fundamental-matrix 3D** path from the Lighthouse RAL 2024 paper, if/when 3D scenes become a priority.

## Don't

- **Don't break the `~/.dotbot/calibration.out` format** without coordinating with `PyDotBot` and announcing a schema version bump.
- **Don't refactor `lighthouse2.py`** numerics without expanding tests first — single test file means easy regressions.
- **Don't merge new SES `.emProject` files** if a CMake/headless build is on the roadmap; instead, extend the headless build to new boards.
