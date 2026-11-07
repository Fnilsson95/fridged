"""Minimal HD44780 (LCD1602) driver, 4-bit mode, write-only, via libgpiod v2."""
import time

import gpiod
from gpiod.line import Direction, Value

# The Pis GPIO controller for Raspberry pi 3
CHIP = "/dev/gpiochip0"

# RS = Register select (0 sends a command, 1 sends character data)
# E = enable (display latches the data lines when E goes high -> low)
RS, E = 25, 24 #
# Data lines
DATA = (23, 12, 16, 20)  # D4..D7


class LCD1602:
    """ A 16x2 LCD on the GPIO pins above. Call close() when done"""

    def __init__(self) -> None:
        pins = (RS, E, *DATA)
        # Claim all six pins as output, starting long. 
        self._req = gpiod.request_lines(
            CHIP,
            consumer="fridged-lcd",
            config={
                p: gpiod.LineSettings(
                    direction=Direction.OUTPUT, output_value=Value.INACTIVE
                )
                for p in pins
            },
        )
        self._init_display()

    def _set(self, pin: int, high: bool) -> None:
        """Drive one pin high or low"""
        self._req.set_value(pin, Value.ACTIVE if high else Value.INACTIVE)

    def _pulse_enable(self) -> None:
        """Tell the display to read the data lines"""
        self._set(E, True)
        time.sleep(0.0001)
        self._set(E, False)
        time.sleep(0.0001)

    def _write_nibble(self, nibble: int) -> None:
        for i, pin in enumerate(DATA):
            self._set(pin, bool(nibble >> i & 1))
        self._pulse_enable()

    def _write_byte(self, value: int, *, data: bool) -> None:
        self._set(RS, data)
        self._write_nibble(value >> 4)
        self._write_nibble(value & 0x0F)
        time.sleep(0.002)  # generous; clear/home need ~1.6 ms

    def _init_display(self) -> None:
        """Wake the display"""
        time.sleep(0.05)
        self._set(RS, False)
        for nibble, delay in ((0x3, 0.005), (0x3, 0.001), (0x3, 0.001), (0x2, 0.001)):
            self._write_nibble(nibble)
            time.sleep(delay)
        self._write_byte(0x28, data=False)  # 4-bit, 2 lines, 5x8 font
        self._write_byte(0x0C, data=False)  # display on, cursor off
        self._write_byte(0x06, data=False)  # cursor moves right
        self.clear()

    def clear(self) -> None:
        """Clear the whole display and move the cursor to the top-left"""
        self._write_byte(0x01, data=False)
        time.sleep(0.003)

    def write(self, text: str, line: int = 0) -> None:
        """Write a text on a line (0 = top, 1 = bottom) padded to 16 characters"""
        self._write_byte(0x80 | (0x40 * line), data=False)  # set DDRAM address
        for ch in text.ljust(16)[:16]:
            self._write_byte(ord(ch), data=True)

    def close(self) -> None:
        """Release the GPIO pins so other programs can use them"""
        self._req.release()