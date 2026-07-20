from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from mapres.datamap import datamap, syntax


def safe_zoneinfo(tz: str):
    try:
        return ZoneInfo(tz)
    except Exception:
        return timezone.utc


@datamap(syntax=syntax.percents, mode='dynamic')
class TimeMap:
    _default_tz = safe_zoneinfo("America/Chicago")

    hh: str | None = None
    h: str | None = None
    h12: str | None = None
    hh12: str | None = None
    ampm: str | None = None
    mm: str | None = None
    m: str | None = None
    ss: str | None = None
    s: str | None = None
    ms: str | None = None
    YYYY: str | None = None
    MM: str | None = None
    DD: str | None = None
    weekday: str | None = None

    def __init__(self, tz: str | None = None):
        self.TZ = safe_zoneinfo(tz) if tz else self._default_tz

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
