"""
Beacon Scanner Module

BLE beacon scanner for ESP32-C3 beacon tracking with SPECS Form integration.
"""

from .beacon_scanner import (
    BeaconScanner,
    ScannerConfig,
    ScanMode,
    BeaconDetection,
    load_beacon_mappings
)

__version__ = "2.0.0"
__all__ = [
    "BeaconScanner",
    "ScannerConfig",
    "ScanMode",
    "BeaconDetection",
    "load_beacon_mappings"
]