"""A fake weather provider used by ex11. Don't edit; import it like a real dependency:

    import provider
    provider.get_temp("Durham")            -> 72
    provider.get_temp("Atlantis")          -> raises provider.UnknownCity("Atlantis")
"""


class UnknownCity(Exception):
    """Raised when the provider has no data for a city. str(e) is the city as given."""


_TEMPS_F = {
    "durham": 72,
    "new york": 65,
    "san luis obispo": 68,
    "raleigh": 74,
}


def get_temp(city: str) -> int:
    temp = _TEMPS_F.get(city.strip().lower())
    if temp is None:
        raise UnknownCity(city)
    return temp
