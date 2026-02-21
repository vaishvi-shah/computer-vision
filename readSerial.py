from microbit import *

# Set up serial to USB (default for most Microbit editors)
# If using MakeCode, serial is redirected to USB by default

while True:
    if uart.any():
        data = uart.read().decode('utf-8').strip()
        if data:
            display.scroll(data)
