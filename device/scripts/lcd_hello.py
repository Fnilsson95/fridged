"""
Test script for the LCD (show two lines of text and exits)
"""

# Import the screen functionality
from fridged.display.lcd1602 import LCD1602

# Claim the GPIO pins and initialise the display
lcd = LCD1602()

try:
    lcd.write("Fridged", 0)  # top line (0)
    lcd.write("Tracker!", 1)  # bottom line (1)
finally:
    lcd.close()
