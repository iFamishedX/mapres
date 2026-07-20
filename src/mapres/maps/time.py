from datetime import datetime
from zoneinfo import ZoneInfo
from mapres.datamap import datamap, syntax


@datamap(syntax=syntax.percents, mode='dynamic')
class TimeMap:
    # default timezone
    try:
        _default_tz = ZoneInfo("America/Chicago")
    except Exception:
        from datetime import timezone
        _default_tz = timezone.utc

    # dynamic fields
    hh: str = None
    h: str = None
    h12: str = None
    hh12: str = None
    ampm: str = None
    mm: str = None
    m: str = None
    ss: str = None
    s: str = None
    ms: str = None
    YYYY: str = None
    MM: str = None
    DD: str = None
    weekday: str = None

    def __init__(self, tz: str | None = None):
        self.TZ = ZoneInfo(tz) if tz else self._default_tz

    @property
    def providers(self):
        now = lambda: datetime.now(self.TZ)

        return {
            # 24-hour formats
            'hh':   lambda: f'{now().hour:02d}',   # 00–23 padded
            'h':    lambda: str(now().hour),       # 0–23 no pad

            # 12-hour formats
            'h12':  lambda: str((now().hour % 12) or 12),              # 1–12 no pad
            'hh12': lambda: f'{(now().hour % 12) or 12:02d}',          # 01–12 padded
            'ampm': lambda: now().strftime('%p'),                      # AM / PM

            # minutes
            'mm':   lambda: f'{now().minute:02d}',  # 00–59 padded
            'm':    lambda: str(now().minute),      # 0–59 no pad

            # seconds
            'ss':   lambda: f'{now().second:02d}',  # 00–59 padded
            's':    lambda: str(now().second),      # 0–59 no pad

            # milliseconds
            'ms':   lambda: f'{int(now().microsecond / 1000):03d}',

            # date
            'YYYY': lambda: str(now().year),
            'MM':   lambda: f'{now().month:02d}',
            'DD':   lambda: f'{now().day:02d}',

            # weekday
            'weekday': lambda: now().strftime('%A'),
        }


# proxy map
time = TimeMap
