"""
Country-to-continent mapping for geographic representativeness analysis.

Provides a single function ``get_continent()`` that handles both single-country
and multi-country strings, replacing the duplicated inline functions that
previously existed in ``03_representativeness.ipynb``.
"""

from __future__ import annotations

import re
from typing import Final

COUNTRY_CONTINENT_MAP: Final[dict[str, str]] = {
    # North America
    "USA": "North America",
    "Canada": "North America",
    # Europe
    "UK": "Europe",
    "Germany": "Europe",
    "Netherlands": "Europe",
    "Spain": "Europe",
    "Italy": "Europe",
    "Switzerland": "Europe",
    "France": "Europe",
    "Denmark": "Europe",
    "Belgium": "Europe",
    "Norway": "Europe",
    "Greece": "Europe",
    "Poland": "Europe",
    "Sweden": "Europe",
    # Asia
    "Japan": "Asia",
    "South Korea": "Asia",
    "Korea": "Asia",
    "Taiwan": "Asia",
    "Thailand": "Asia",
    "China": "Asia",
    "India": "Asia",
    # Oceania
    "Australia": "Oceania",
    "New Zealand": "Oceania",
    # South America
    "Brazil": "South America",
    "Mexico": "South America",
    "Chile": "South America",
    # Africa
    "South Africa": "Africa",
    "Egypt": "Africa",
}


def get_continent(country_str: str | None) -> str:
    """Resolve a country or multi-country string to a single continent label.

    Steps
    -----
    1. **Exact match** — if *country_str* is a key in
       :data:`COUNTRY_CONTINENT_MAP`, return the mapped continent immediately.
    2. **Multi-country parse** — strip the ``"Europe (…)"`` wrapper if present,
       then split on ``,`` or ``" and "``.  Each fragment is resolved via exact
       match, then substring match against map keys.
    3. **Verdict** — all same continent → that continent; mixed → ``"Multi-continent"``;
       unresolvable → ``"Other"``; ``None``/``NaN`` → ``"Unknown"``.

    Parameters
    ----------
    country_str : str or None
        Raw country string from the dataset (e.g. ``"Netherlands"``,
        ``"Belgium and Spain"``, ``"Europe (Belgium, Greece, UK)"``).

    Returns
    -------
    str
        One of ``"North America"``, ``"Europe"``, ``"Asia"``, ``"Oceania"``,
        ``"South America"``, ``"Africa"``, ``"Multi-continent"``, ``"Other"``,
        or ``"Unknown"``.
    """
    if country_str is None:
        return "Unknown"

    country_str = str(country_str).strip()

    # ---- 1. Exact match (handles all single countries) -----------------------
    if country_str in COUNTRY_CONTINENT_MAP:
        return COUNTRY_CONTINENT_MAP[country_str]

    # ---- 2. Parse multi-country strings --------------------------------------
    s = country_str

    # Strip "Europe (x, y, z)" wrapper → "x, y, z"
    if s.startswith("Europe ("):
        s = s.removeprefix("Europe (").removesuffix(")")

    # Split on commas or " and "
    parts = [p.strip() for p in re.split(r",| and ", s) if p.strip()]
    if not parts:
        return "Other"

    continents: set[str] = set()
    for part in parts:
        # Exact match on fragment
        if part in COUNTRY_CONTINENT_MAP:
            continents.add(COUNTRY_CONTINENT_MAP[part])
            continue
        # Substring fallback (e.g. part = "Belgium" found via "Belgium" in "Belgium and Spain")
        matched = False
        for name, continent in COUNTRY_CONTINENT_MAP.items():
            if name in part:
                continents.add(continent)
                matched = True
                break
        if not matched:
            return "Other"  # fragment could not be resolved to any country

    if len(continents) == 1:
        return continents.pop()
    if len(continents) > 1:
        return "Multi-continent"
    return "Unknown"
