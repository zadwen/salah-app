"""Client for the Aladhan prayer-times API, and IP-based geolocation.

Uses only the Python standard library (urllib) so the app has zero
third-party pip dependencies beyond PyGObject (a system package).
"""
import datetime
import json
import os
import urllib.error
import urllib.parse
import urllib.request

from . import config as cfgmod

ALADHAN_BASE = "https://api.aladhan.com/v1"
IPAPI_CO_URL = "https://ipapi.co/json/"
IP_API_COM_URL = "http://ip-api.com/json/"
USER_AGENT = "salah-app/1.0 (+https://github.com/)"

PRAYER_KEYS = ["Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"]


class ApiError(Exception):
    pass


def _http_get_json(url, timeout=10):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
        return json.loads(data.decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        raise ApiError(f"{url}: {e}")
    except json.JSONDecodeError as e:
        raise ApiError(f"{url}: invalid response ({e})")


def detect_location_by_ip():
    """Best-effort auto location using IP geolocation.

    Tries ipapi.co first, then falls back to ip-api.com (some ISPs /
    firewalls block one but not the other). Returns dict or raises
    ApiError with details from the last attempt so the UI can show a
    useful message instead of a silent failure.
    """
    errors = []

    try:
        data = _http_get_json(IPAPI_CO_URL)
        if data.get("error"):
            raise ApiError(data.get("reason", "ipapi.co returned an error"))
        if data.get("latitude") is not None:
            return {
                "lat": data.get("latitude"),
                "lon": data.get("longitude"),
                "city": data.get("city", "") or "",
                "country": data.get("country_name", "") or "",
            }
        errors.append("ipapi.co: no coordinates in response")
    except ApiError as e:
        errors.append(str(e))

    try:
        data = _http_get_json(IP_API_COM_URL)
        if data.get("status") == "success" and data.get("lat") is not None:
            return {
                "lat": data.get("lat"),
                "lon": data.get("lon"),
                "city": data.get("city", "") or "",
                "country": data.get("country", "") or "",
            }
        errors.append(f"ip-api.com: {data.get('message', 'no coordinates')}")
    except ApiError as e:
        errors.append(str(e))

    raise ApiError("Auto-location failed. " + " | ".join(errors))


def _cache_path(iso_date, lat, lon, method):
    cfgmod.ensure_dirs()
    key = f"timings_{iso_date}_{lat}_{lon}_{method}.json".replace("/", "_")
    return os.path.join(cfgmod.CACHE_DIR, key)


def get_timings(lat, lon, method=2, date=None, use_cache=True):
    """Fetch prayer timings + hijri date for given coords/date.

    Results are cached to disk per-day so the widget doesn't hit the
    network more than once a day per location/method combination.
    """
    if date is None:
        date = datetime.date.today()
    date_str = date.strftime("%d-%m-%Y")
    cache_file = _cache_path(date.isoformat(), lat, lon, method)

    if use_cache and os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    params = urllib.parse.urlencode({
        "latitude": lat,
        "longitude": lon,
        "method": method,
    })
    url = f"{ALADHAN_BASE}/timings/{date_str}?{params}"
    data = _http_get_json(url)
    if data.get("code") != 200:
        raise ApiError(f"Aladhan API error: {data.get('status')}")

    d = data["data"]
    result = {
        "timings": {k: v for k, v in d["timings"].items() if k in PRAYER_KEYS},
        "hijri": d["date"]["hijri"],
        "gregorian": d["date"]["gregorian"],
        "date": date.isoformat(),
    }
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    return result


def _cache_path_city(iso_date, city, country, method):
    cfgmod.ensure_dirs()
    key = f"timingsbycity_{iso_date}_{city}_{country}_{method}.json".replace("/", "_").replace(" ", "_")
    return os.path.join(cfgmod.CACHE_DIR, key)


def get_timings_by_city(city, country, method=2, date=None, use_cache=True):
    """Fetch prayer timings by city/country name directly (no lat/lon
    needed) via Aladhan's /timingsByCity endpoint. Useful when the
    user enters a location manually rather than relying on IP-based
    geolocation."""
    if not city or not country:
        raise ApiError("Both city and country are required")
    if date is None:
        date = datetime.date.today()
    date_str = date.strftime("%d-%m-%Y")
    cache_file = _cache_path_city(date.isoformat(), city, country, method)

    if use_cache and os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    params = urllib.parse.urlencode({
        "city": city,
        "country": country,
        "method": method,
    })
    url = f"{ALADHAN_BASE}/timingsByCity/{date_str}?{params}"
    data = _http_get_json(url)
    if data.get("code") != 200:
        raise ApiError(f"Aladhan API error: {data.get('status')}")

    d = data["data"]
    result = {
        "timings": {k: v for k, v in d["timings"].items() if k in PRAYER_KEYS},
        "hijri": d["date"]["hijri"],
        "gregorian": d["date"]["gregorian"],
        "date": date.isoformat(),
        "lat": d.get("meta", {}).get("latitude"),
        "lon": d.get("meta", {}).get("longitude"),
    }
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    return result


def parse_time_today(time_str, base_date=None):
    """Aladhan returns times like '05:12 (+03)' or '05:12'. Parse to a
    timezone-naive datetime on base_date (defaults to today), assuming
    local system time (the API already returns local time for the
    given coordinates)."""
    hhmm = time_str.split(" ")[0]
    h, m = map(int, hhmm.split(":"))
    d = base_date or datetime.date.today()
    return datetime.datetime.combine(d, datetime.time(hour=h, minute=m))
