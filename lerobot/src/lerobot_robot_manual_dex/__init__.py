"""Auto-discovered LeRobot plugin; importing never connects to hardware or accepts terms."""
from .glove import ManualDexGlove, ManualDexGloveConfig
from .sim_robot import ManualDexSim, ManualDexSimConfig
from .hardware import ManualDexHardware, ManualDexHardwareConfig

__all__ = ["ManualDexGlove", "ManualDexGloveConfig", "ManualDexSim", "ManualDexSimConfig",
           "ManualDexHardware", "ManualDexHardwareConfig"]
