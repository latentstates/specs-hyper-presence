"""
SPECS Form API Client

A Python client library for the SPECS Form External Data API.
"""

from .client import (
    SPECSFormClient,
    ExperimentData,
    create_client,
    submit_beacon_detection,
    calculate_quality_score,
    get_signal_quality
)

__version__ = "1.0.0"
__all__ = [
    "SPECSFormClient",
    "ExperimentData", 
    "create_client",
    "submit_beacon_detection",
    "calculate_quality_score",
    "get_signal_quality"
]