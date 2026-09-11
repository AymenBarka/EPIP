"""Immutable P04 Elliott/Fibonacci wave-3 profile configuration."""

PROFILE_ID = "elliott-fibonacci-wave3"
PROFILE_VERSION = "1.0.0"
PROFILE_REFERENCE = f"{PROFILE_ID}@{PROFILE_VERSION}"

ENTRY_RATIOS = (0.618, 0.705)
TARGET_RATIO = 1.618
MINIMUM_RR = 3.0
ELLIOTT_WEIGHT = 0.60
FIBONACCI_WEIGHT = 0.40
MINIMUM_CONFIDENCE = 0.70
EXPIRATION_SECONDS = 300
NUMERIC_PRECISION = 2

REQUIRED_SOURCE_DOMAINS = ("ELLIOTT", "FIBONACCI", "MARKET_STRUCTURE")
EVIDENCE_KEYS = (
    "elliott.wave3_setup",
    "fibonacci.w1_anchor",
    "structure.direction_alignment",
    "entry.golden_0618_0705",
    "stop.wave1_origin",
    "target.extension_1618",
    "confidence.elliott_fibonacci_60_40",
)

__all__ = [
    "ELLIOTT_WEIGHT",
    "ENTRY_RATIOS",
    "EVIDENCE_KEYS",
    "EXPIRATION_SECONDS",
    "FIBONACCI_WEIGHT",
    "MINIMUM_CONFIDENCE",
    "MINIMUM_RR",
    "NUMERIC_PRECISION",
    "PROFILE_ID",
    "PROFILE_REFERENCE",
    "PROFILE_VERSION",
    "REQUIRED_SOURCE_DOMAINS",
    "TARGET_RATIO",
]
