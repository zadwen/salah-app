"""Core scheduling logic: fetches today's timings, works out what the
next prayer is, formats countdowns, and decides when reminder /
at-time notifications are due. Kept independent of GTK so it's easy
to unit-test.
"""
import datetime

from . import api
from .constants import PRAYER_ORDER, REMINDABLE_PRAYERS


class DayPlan:
    """Holds today's prayer times as datetimes, plus convenience lookups."""

    def __init__(self, timings_raw, base_date=None):
        self.base_date = base_date or datetime.date.today()
        self.times = {}
        for name in PRAYER_ORDER:
            raw = timings_raw.get(name)
            if raw:
                self.times[name] = api.parse_time_today(raw, self.base_date)
        self.hijri = None
        self.gregorian = None
        self.lat = None
        self.lon = None

    def ordered_upcoming(self, now=None):
        """Return list of (name, dt) pairs still in the future today,
        in chronological order."""
        now = now or datetime.datetime.now()
        return [(n, self.times[n]) for n in PRAYER_ORDER
                if n in self.times and self.times[n] > now]

    def next_prayer(self, now=None):
        """Return (name, dt) of the next upcoming prayer today, or
        None if all of today's prayers have passed (caller should
        roll over to tomorrow's plan)."""
        upcoming = self.ordered_upcoming(now)
        return upcoming[0] if upcoming else None

    def next_remindable(self, now=None):
        now = now or datetime.datetime.now()
        candidates = [(n, self.times[n]) for n in REMINDABLE_PRAYERS
                      if n in self.times and self.times[n] > now]
        return candidates[0] if candidates else None


def format_countdown(delta: datetime.timedelta, lang="en"):
    total_seconds = max(0, int(delta.total_seconds()))
    hours, rem = divmod(total_seconds, 3600)
    minutes, _ = divmod(rem, 60)
    if lang == "ar":
        if hours > 0:
            return f"{hours} س {minutes} د"
        return f"{minutes} د"
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def load_day_plan(lat, lon, method, date=None, use_cache=True):
    data = api.get_timings(lat, lon, method=method, date=date, use_cache=use_cache)
    plan = DayPlan(data["timings"], base_date=date or datetime.date.today())
    plan.hijri = data.get("hijri")
    plan.gregorian = data.get("gregorian")
    return plan


def load_day_plan_by_city(city, country, method, date=None, use_cache=True):
    """Same as load_day_plan but resolves the location by city/country
    name via Aladhan directly, without needing lat/lon. The response
    also carries back the resolved lat/lon (used for the Qibla
    calculation) in plan.lat / plan.lon."""
    data = api.get_timings_by_city(city, country, method=method, date=date, use_cache=use_cache)
    plan = DayPlan(data["timings"], base_date=date or datetime.date.today())
    plan.hijri = data.get("hijri")
    plan.gregorian = data.get("gregorian")
    plan.lat = data.get("lat")
    plan.lon = data.get("lon")
    return plan
