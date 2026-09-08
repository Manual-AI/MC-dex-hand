"""Interface example only. Intentionally cannot open a port or move a motor."""


class HandDriverTemplate:
    hardware_watchdog_supported = False

    def __init__(self, *, port, profile):
        self.port, self.profile = port, profile

    def connect(self, *, read_only):
        raise NotImplementedError("Implement verified HLS3606 communication, identity checks and read-only connection")

    def read_positions_rad(self):
        raise NotImplementedError("Return fresh measured encoder positions mapped to the eight named CAD-frame radians")

    def arm(self, *, watchdog_s, hold_positions):
        raise NotImplementedError("Configure a controller-side watchdog and hold the measured current pose")

    def send_positions_rad(self, positions):
        raise NotImplementedError("Convert radians to confirmed encoder units; apply controller limits and refresh watchdog")

    def stop(self):
        # Implement the tested safe-stop policy for your mechanics/controller.
        pass

    def disconnect(self):
        pass
