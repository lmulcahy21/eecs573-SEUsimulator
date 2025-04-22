import numpy as np

class TimingInfo:
    def __init__(self, clock_period_ns: float, setup_time_ns: float, hold_time_ns: float):
        self.clock_period_ns = clock_period_ns
        self.clock_period_ps = np.round(clock_period_ns * 1000)

        self.setup_time_ns = setup_time_ns
        self.setup_time_ps = np.round(setup_time_ns * 1000)

        self.hold_time_ns = hold_time_ns
        self.hold_time_ps = np.round(hold_time_ns * 1000)