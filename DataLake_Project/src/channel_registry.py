"""Channel registry and enrichment metadata for TV now_playing data."""

# Mapping of channel variants to canonical names and metadata
CHANNEL_REGISTRY = {
    # Our team channels
    "hbo_3": {
        "canonical": "HBO3",
        "country": "SK",
        "language": "SK",
        "content_type": "movies_series",
        "variants": ["hbo_3", "hbo-3", "hbo 3"]
    },
    "cinemax": {
        "canonical": "CINEMAX",
        "country": "SK",
        "language": "SK",
        "content_type": "movies",
        "variants": ["cinemax", "cinemax_2"]
    },
    "cinemax_2": {
        "canonical": "CINEMAX",
        "country": "SK",
        "language": "SK",
        "content_type": "movies",
        "variants": ["cinemax", "cinemax_2"]
    },

    # Team1 (TUKE) channels
    "hbo": {
        "canonical": "HBO",
        "country": "SK",
        "language": "SK",
        "content_type": "movies_series",
        "variants": ["hbo", "hbo_1"]
    },
    "joj-cinema": {
        "canonical": "JOJ_CINEMA",
        "country": "SK",
        "language": "SK",
        "content_type": "movies",
        "variants": ["joj-cinema", "joj_cinema"]
    },
    "film-plus": {
        "canonical": "FILM_PLUS",
        "country": "SK",
        "language": "SK",
        "content_type": "movies",
        "variants": ["film-plus", "film_plus"]
    },

    # Team2 channels
    "hbo-2": {
        "canonical": "HBO2",
        "country": "SK",
        "language": "SK",
        "content_type": "movies_series",
        "variants": ["hbo-2", "hbo_2", "hbo 2"]
    },
    "nova-cinema": {
        "canonical": "NOVA_CINEMA",
        "country": "SK",
        "language": "SK",
        "content_type": "movies",
        "variants": ["nova-cinema", "nova_cinema"]
    },
    "filmbox": {
        "canonical": "FILMBOX",
        "country": "SK",
        "language": "SK",
        "content_type": "movies",
        "variants": ["filmbox", "film-box"]
    },

    # Team3 channels
    "dajto": {
        "canonical": "DAJTO",
        "country": "SK",
        "language": "SK",
        "content_type": "series_entertainment",
        "variants": ["dajto"]
    },
    "prima-sk": {
        "canonical": "PRIMA",
        "country": "SK",
        "language": "SK",
        "content_type": "general",
        "variants": ["prima-sk", "prima_sk"]
    },
    "markiza-krimi": {
        "canonical": "MARKIZA_KRIMI",
        "country": "SK",
        "language": "SK",
        "content_type": "series",
        "variants": ["markiza-krimi", "markiza_krimi"]
    },
}

# Create reverse mapping: variant -> canonical info
VARIANT_TO_CANONICAL = {}
for canonical_key, info in CHANNEL_REGISTRY.items():
    for variant in info["variants"]:
        VARIANT_TO_CANONICAL[variant.lower()] = {
            "canonical": info["canonical"],
            "country": info["country"],
            "language": info["language"],
            "content_type": info["content_type"]
        }

def get_channel_info(channel_name: str | None) -> dict:
    """
    Get canonical channel info from a channel name variant.

    Args:
        channel_name: Channel name (any variant)

    Returns:
        Dict with canonical, country, language, content_type.
        If not found, returns a safe default.
    """
    if not channel_name:
        return {
            "canonical": "UNKNOWN",
            "country": "SK",
            "language": "SK",
            "content_type": "unknown"
        }

    normalized = str(channel_name).lower().strip().replace("_", "-")
    return VARIANT_TO_CANONICAL.get(
        normalized,
        {
            "canonical": channel_name.upper(),
            "country": "SK",
            "language": "SK",
            "content_type": "unknown"
        }
    )

def extract_team_from_source(source: str | None) -> str:
    """Extract team name from source identifier."""
    if not source:
        return "unknown"

    source_lower = str(source).lower()

    if source_lower.startswith("ours"):
        return "ours"
    elif "team1" in source_lower or "tuke" in source_lower:
        return "team1"
    elif "team2" in source_lower:
        return "team2"
    elif "team3" in source_lower:
        return "team3"
    elif "team4" in source_lower:
        return "team4"
    else:
        return "unknown"
