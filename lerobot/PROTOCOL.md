# Proposed glove serial contract: `manual-dex-glove-v1`

This is the interface implemented by the new host adapter. **It is not a claim about
existing firmware**: the ESP32 source, pin map and verified acquisition circuit are
not yet released. A firmware author must implement and test this contract.

## Transport and fields

USB serial, 115200 baud, 8 data bits, no parity, 1 stop bit. Send one UTF-8 JSON object
per line, terminated by `\n`, at 60 Hz or faster. Each line must be shorter than
4096 bytes. Diagnostic messages must not share the measurement stream.

[`configs/protocol_frame.example.json`](configs/protocol_frame.example.json) shows one
packet formatted for reading. On the wire, serialize that object onto **one line**:

| Field | Contract |
|---|---|
| `schema` | Exact string `manual-dex-glove-v1` |
| `device_id` | Stable string matching `--teleop.id`; unique per glove |
| `seq` | Strictly increasing integer, one increment per acquired frame |
| `device_ms` | Strictly increasing integer acquisition timestamp in device milliseconds |
| `raw` | Exactly the eight names in [CALIBRATION.md](CALIBRATION.md), each a finite ADC count in 0–4095 |

Acquire all channels as one frame and timestamp acquisition, not delayed transmission.
Never fabricate fresh counters for an old sensor frame. Account for ESP32 ADC channel
restrictions, input voltage limits, noise and attenuation in the verified electronics
design; this host protocol does not configure the board or choose safe wiring.
Do not copy ADC pins from an unrelated board variant.

Use counters wide enough for the session. Device reset or counter wrap requires an
explicit host reconnect; decreasing/repeated values are rejected. Reset/restart must
never be hidden by reusing cached readings. Counter checks detect obvious replay or
stalls; this is **not** an authenticated transport or a certified safety system.

## Host behavior

The host reads only the explicitly configured port; it sends no motor or firmware
configuration commands. Opening a USB serial port can still toggle DTR/RTS and reset
some ESP32 boards. Verify your board's reset behavior before use; opening the glove
port must never enable hand torque.

Before each read, the host discards buffered bytes and waits for a fresh complete
line. A partial line after flushing is dropped. Wrong schema/device ID, invalid
channels or non-monotonic counters abort the read. No fresh line before `timeout_s`
(default 0.25 s) raises an error and ends the teleoperation loop. There is no wireless
reconnect, automatic device discovery or automatic re-arming.

A host timeout alone cannot stop a hand if Python, USB or the host computer fails.
Physical deployment requires the separately tested controller-side watchdog and
emergency stop described in [HARDWARE.md](HARDWARE.md).
