"""Where this thing pretends to run. Currently: Europe, allegedly."""

import os

# Set DEPLOY_REGION to any key below. Anything else falls back to eu-west-1,
# because the committee does not operate outside the Union.
REGIONS = {
    "eu-west-1":    {"city": "Dublin",   "country": "IE", "timezone": "Europe/Dublin"},
    "eu-west-3":    {"city": "Paris",    "country": "FR", "timezone": "Europe/Paris"},
    "eu-central-1": {"city": "Frankfurt","country": "DE", "timezone": "Europe/Berlin"},
    "eu-south-1":   {"city": "Milan",    "country": "IT", "timezone": "Europe/Rome"},
    "eu-north-1":   {"city": "Stockholm","country": "SE", "timezone": "Europe/Stockholm"},
}

DEFAULT_REGION = "eu-west-1"

REGION = os.environ.get("DEPLOY_REGION", DEFAULT_REGION)
if REGION not in REGIONS:
    REGION = DEFAULT_REGION

CITY = REGIONS[REGION]["city"]
COUNTRY = REGIONS[REGION]["country"]
TIMEZONE = REGIONS[REGION]["timezone"]

# Nothing leaves the continent. Not even the bad CVs.
DATA_RESIDENCY = "EU"
LOCALE = os.environ.get("DEPLOY_LOCALE", "en-IE")
CURRENCY = "EUR"

# Days a submitted curriculum would be retained, if we retained anything.
RETENTION_DAYS = 30


def info() -> dict:
    """The block every /api/health and footer wants."""
    return {
        "region": REGION,
        "city": CITY,
        "country": COUNTRY,
        "timezone": TIMEZONE,
        "data_residency": DATA_RESIDENCY,
        "locale": LOCALE,
        "currency": CURRENCY,
        "gdpr": True,
        "retention_days": RETENTION_DAYS,
    }


def headers() -> list:
    """Response headers that let an operator see the region without asking."""
    return [
        ("X-Deployment-Region", REGION),
        ("X-Data-Residency", DATA_RESIDENCY),
        ("X-Deployment-Timezone", TIMEZONE),
    ]
