"""Static reference data used across the app."""

# Aladhan API calculation method IDs -> human readable label
CALCULATION_METHODS = {
    2: "Islamic Society of North America (ISNA)",
    3: "Muslim World League (MWL)",
    4: "Umm al-Qura, Makkah",
    5: "Egyptian General Authority of Survey",
    1: "University of Islamic Sciences, Karachi",
    7: "Institute of Geophysics, Tehran",
    8: "Gulf Region",
    9: "Kuwait",
    10: "Qatar",
    11: "Majlis Ugama Islam Singapura",
    12: "Union Organization Islamic de France",
    13: "Diyanet (Turkey)",
    14: "Spiritual Administration of Muslims of Russia",
    15: "Moonsighting Committee Worldwide",
    16: "Dubai (unofficial)",
}

DEFAULT_METHOD = 2

# Kaaba coordinates, used for Qibla bearing calculation
KAABA_LAT = 21.4225
KAABA_LON = 39.8262

PRAYER_ORDER = ["Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"]

# Prayers that actually get a "time to pray" reminder (Sunrise is informational only)
REMINDABLE_PRAYERS = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
