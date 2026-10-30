# Device daemon (`fridged`)

Python daemon for the Raspberry Pi: reads the USB scanner, handles command cards locally, posts scans to the backend, drives LED, buzzer, buttons and LCD, and queues scans offline.

Keep scanner input in `src/fridged/scanner/` behind a narrow interface so it can be rewritten in C++ later.
