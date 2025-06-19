#!/usr/bin/env python3
"""
Beacon Scanner for SPECS Form Integration

A unified BLE beacon scanner with multiple operational modes for tracking
ESP32-C3 beacons and submitting data to SPECS Form External Data API.
"""
import asyncio
import json
import logging
import os
import sys
import time
import random
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Add parent directory to path for specs_client import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from bleak import BleakScanner
    from bleak.backends.device import BLEDevice
    from bleak.backends.scanner import AdvertisementData
    BLEAK_AVAILABLE = True
except ImportError:
    BLEAK_AVAILABLE = False
    print("Warning: bleak not installed. BLE scanning disabled. Install with: pip install bleak")

try:
    from specs_client.client import create_client, submit_beacon_detection, ExperimentData
    SPECSFORM_API_AVAILABLE = True
except ImportError:
    SPECSFORM_API_AVAILABLE = False
    print("Warning: specs_client not available. API submission disabled.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ScanMode(Enum):
    """Scanner operational modes"""
    SIMPLE = "simple"      # Mock data, no BLE required
    STANDARD = "standard"  # Basic BLE scanning
    ENHANCED = "enhanced"  # Advanced filtering and quality metrics
    BATCH = "batch"        # Batch submission mode


@dataclass
class BeaconDetection:
    """Represents a beacon detection event"""
    mac_address: str
    rssi: float
    timestamp: datetime
    scanner_location: str
    memorable_id: Optional[str] = None
    participant_id: Optional[str] = None
    raw_data: Optional[Dict] = None


@dataclass
class ScannerConfig:
    """Scanner configuration"""
    # API settings
    api_url: str = "http://localhost:8001"
    api_key: str = "sk_prod_7K9mXvN2pQ5rT8wY3hL6jF4aB1cD"
    
    # Scanner settings
    mode: ScanMode = ScanMode.STANDARD
    location: str = "default-location"
    producer_id: str = "beacon-scanner-01"
    organization: str = "Research Lab"
    
    # Scan parameters
    scan_interval: int = 30  # seconds between scans
    scan_duration: int = 10  # seconds per scan
    batch_size: int = 50     # detections per batch
    batch_interval: int = 300  # seconds between batch submissions
    
    # Filtering
    rssi_threshold: float = -90.0  # minimum RSSI to consider
    quality_threshold: float = 0.3  # minimum quality score
    
    # Beacon mappings
    beacon_mappings: Dict[str, str] = field(default_factory=dict)
    
    # Features
    enable_caching: bool = True
    enable_filtering: bool = True
    mock_beacons: bool = False
    dry_run: bool = False


class BeaconScanner:
    """Unified beacon scanner with multiple operational modes"""
    
    def __init__(self, config: ScannerConfig):
        self.config = config
        self.client = None
        self.is_registered = False
        self.detection_cache: List[BeaconDetection] = []
        self.participant_cache: Dict[str, str] = {}  # memorable_id -> participant_id
        self.seen_beacons: Set[str] = set()
        self.last_batch_time = datetime.now()
        
        # Initialize API client if available
        if SPECSFORM_API_AVAILABLE and not config.dry_run:
            self.client = create_client(config.api_url, config.api_key)
            if not self.client.health_check():
                logger.warning("API server not reachable. Running in offline mode.")
                self.client = None
    
    async def initialize(self) -> bool:
        """Initialize scanner and register with API"""
        logger.info(f"Initializing scanner in {self.config.mode.value} mode")
        logger.info(f"Location: {self.config.location}")
        logger.info(f"Producer ID: {self.config.producer_id}")
        
        if self.client and not self.is_registered:
            # Get project
            projects = self.client.list_projects()
            if not projects:
                logger.error("No projects available in SPECS Form")
                return False
            
            project_id = projects[0]["id"]
            logger.info(f"Using project: {projects[0]['display_name']}")
            
            # Register producer
            self.is_registered = self.client.register_producer(
                producer_id=self.config.producer_id,
                name=f"Beacon Scanner - {self.config.location}",
                producer_type="beacon_scanner",
                project_id=project_id,
                organization=self.config.organization,
                version="2.0",
                config={
                    "mode": self.config.mode.value,
                    "location": self.config.location,
                    "scan_interval": self.config.scan_interval,
                    "features": {
                        "caching": self.config.enable_caching,
                        "filtering": self.config.enable_filtering,
                        "batch_mode": self.config.mode == ScanMode.BATCH
                    }
                }
            )
            
            if self.is_registered:
                logger.info("✅ Registered with SPECS Form API")
            else:
                logger.warning("Failed to register producer. Continuing anyway.")
        
        return True
    
    async def scan_ble_devices(self) -> List[BeaconDetection]:
        """Scan for BLE devices using bleak"""
        if not BLEAK_AVAILABLE:
            return []
        
        detections = []
        start_time = datetime.now()
        
        logger.info(f"Starting BLE scan for {self.config.scan_duration}s...")
        
        try:
            devices = await BleakScanner.discover(
                timeout=self.config.scan_duration,
                return_adv=True
            )
            
            for device, adv_data in devices.values():
                # Filter by RSSI threshold
                rssi = adv_data.rssi
                if rssi < self.config.rssi_threshold:
                    continue
                
                # Create detection
                detection = BeaconDetection(
                    mac_address=device.address.upper(),
                    rssi=rssi,
                    timestamp=datetime.now(),
                    scanner_location=self.config.location,
                    raw_data={
                        "name": device.name,
                        "manufacturer_data": dict(adv_data.manufacturer_data),
                        "service_data": dict(adv_data.service_data),
                        "service_uuids": list(adv_data.service_uuids)
                    }
                )
                
                # Map to participant if configured
                if device.address.upper() in self.config.beacon_mappings:
                    detection.memorable_id = self.config.beacon_mappings[device.address.upper()]
                
                detections.append(detection)
                
                # Track unique beacons
                self.seen_beacons.add(device.address.upper())
            
            logger.info(f"Detected {len(detections)} beacons")
            
        except Exception as e:
            logger.error(f"BLE scan error: {e}")
        
        return detections
    
    def generate_mock_detections(self) -> List[BeaconDetection]:
        """Generate mock beacon detections for testing"""
        mock_beacons = {
            "AA:BB:CC:DD:EE:01": "soft-plum-snake",
            "AA:BB:CC:DD:EE:02": "brave-amber-lynx",
            "AA:BB:CC:DD:EE:03": "quick-jade-fox",
        }
        
        detections = []
        for mac, memorable_id in mock_beacons.items():
            # Random chance of detection
            if random.random() > 0.3:  # 70% chance
                detection = BeaconDetection(
                    mac_address=mac,
                    rssi=random.uniform(-80, -40),
                    timestamp=datetime.now(),
                    scanner_location=self.config.location,
                    memorable_id=memorable_id
                )
                detections.append(detection)
                self.seen_beacons.add(mac)
        
        logger.info(f"Generated {len(detections)} mock detections")
        return detections
    
    async def get_detections(self) -> List[BeaconDetection]:
        """Get beacon detections based on mode"""
        if self.config.mode == ScanMode.SIMPLE or self.config.mock_beacons:
            return self.generate_mock_detections()
        else:
            return await self.scan_ble_devices()
    
    def apply_enhanced_filtering(self, detections: List[BeaconDetection]) -> List[BeaconDetection]:
        """Apply enhanced filtering for quality"""
        if not self.config.enable_filtering:
            return detections
        
        filtered = []
        
        # Group by MAC address
        by_mac = {}
        for d in detections:
            if d.mac_address not in by_mac:
                by_mac[d.mac_address] = []
            by_mac[d.mac_address].append(d)
        
        # Filter each group
        for mac, group in by_mac.items():
            if len(group) == 1:
                filtered.append(group[0])
            else:
                # Average RSSI for multiple detections
                avg_rssi = sum(d.rssi for d in group) / len(group)
                # Use most recent detection with averaged RSSI
                latest = max(group, key=lambda d: d.timestamp)
                latest.rssi = avg_rssi
                filtered.append(latest)
        
        return filtered
    
    async def lookup_participant(self, memorable_id: str) -> Optional[str]:
        """Look up participant ID with caching"""
        if memorable_id in self.participant_cache:
            return self.participant_cache[memorable_id]
        
        if self.client:
            participant = self.client.lookup_participant(memorable_id=memorable_id)
            if participant:
                participant_id = participant["participant_id"]
                self.participant_cache[memorable_id] = participant_id
                return participant_id
        
        return None
    
    async def submit_detection(self, detection: BeaconDetection) -> bool:
        """Submit a single detection to the API"""
        if self.config.dry_run:
            logger.info(f"[DRY RUN] Would submit: {detection.mac_address} at {detection.scanner_location}")
            return True
        
        if not self.client:
            return False
        
        # Look up participant if needed
        if detection.memorable_id and not detection.participant_id:
            detection.participant_id = await self.lookup_participant(detection.memorable_id)
        
        if not detection.participant_id:
            logger.warning(f"No participant found for {detection.mac_address}")
            return False
        
        # Submit using convenience function
        success = submit_beacon_detection(
            client=self.client,
            participant_id=detection.participant_id,
            location=detection.scanner_location,
            mac_address=detection.mac_address,
            rssi=detection.rssi,
            producer_id=self.config.producer_id
        )
        
        if success:
            logger.debug(f"Submitted detection: {detection.mac_address}")
        else:
            logger.error(f"Failed to submit detection: {detection.mac_address}")
        
        return success
    
    async def submit_batch(self, detections: List[BeaconDetection]) -> int:
        """Submit a batch of detections"""
        if not detections:
            return 0
        
        logger.info(f"Submitting batch of {len(detections)} detections")
        
        success_count = 0
        for detection in detections:
            if await self.submit_detection(detection):
                success_count += 1
        
        logger.info(f"Successfully submitted {success_count}/{len(detections)} detections")
        return success_count
    
    async def run_scan_cycle(self) -> int:
        """Run a single scan cycle"""
        # Get detections
        detections = await self.get_detections()
        
        # Apply filtering if in enhanced mode
        if self.config.mode == ScanMode.ENHANCED:
            detections = self.apply_enhanced_filtering(detections)
        
        # Handle based on mode
        if self.config.mode == ScanMode.BATCH:
            # Add to cache for batch submission
            self.detection_cache.extend(detections)
            
            # Check if batch submission needed
            time_since_batch = (datetime.now() - self.last_batch_time).seconds
            if (len(self.detection_cache) >= self.config.batch_size or 
                time_since_batch >= self.config.batch_interval):
                
                submitted = await self.submit_batch(self.detection_cache)
                self.detection_cache.clear()
                self.last_batch_time = datetime.now()
                return submitted
            
            return 0
        else:
            # Submit immediately
            return await self.submit_batch(detections)
    
    async def run(self):
        """Main scanner loop"""
        logger.info("=" * 60)
        logger.info("🔵 Beacon Scanner Starting")
        logger.info("=" * 60)
        
        # Initialize
        if not await self.initialize():
            logger.error("Failed to initialize scanner")
            return
        
        logger.info(f"Scan interval: {self.config.scan_interval}s")
        logger.info(f"Scan duration: {self.config.scan_duration}s")
        
        if self.config.mode == ScanMode.BATCH:
            logger.info(f"Batch size: {self.config.batch_size}")
            logger.info(f"Batch interval: {self.config.batch_interval}s")
        
        logger.info("-" * 60)
        
        # Main loop
        try:
            scan_count = 0
            total_submitted = 0
            
            while True:
                scan_count += 1
                logger.info(f"\n🔍 Scan #{scan_count} at {datetime.now():%H:%M:%S}")
                
                submitted = await self.run_scan_cycle()
                total_submitted += submitted
                
                # Status update
                logger.info(f"📊 Unique beacons seen: {len(self.seen_beacons)}")
                logger.info(f"📤 Total submitted: {total_submitted}")
                
                if self.config.mode == ScanMode.BATCH and self.detection_cache:
                    logger.info(f"📦 Cached for batch: {len(self.detection_cache)}")
                
                # Wait for next scan
                await asyncio.sleep(self.config.scan_interval)
                
        except KeyboardInterrupt:
            logger.info("\n⚠️  Scanner stopped by user")
            
            # Submit any remaining cached detections
            if self.config.mode == ScanMode.BATCH and self.detection_cache:
                logger.info("Submitting remaining cached detections...")
                await self.submit_batch(self.detection_cache)
        
        finally:
            if self.client:
                self.client.close()


def load_beacon_mappings(file_path: str) -> Dict[str, str]:
    """Load beacon mappings from JSON file"""
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return {}


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Beacon Scanner for SPECS Form Integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simple mode (mock data)
  %(prog)s --mode simple --location entrance

  # Standard BLE scanning
  %(prog)s --mode standard --location lab-room-a

  # Enhanced mode with filtering
  %(prog)s --mode enhanced --location hallway --rssi-threshold -70

  # Batch mode
  %(prog)s --mode batch --batch-size 100 --batch-interval 600

  # Dry run (no API submission)
  %(prog)s --dry-run --mode standard
        """
    )
    
    # Mode selection
    parser.add_argument(
        "--mode", "-m",
        type=str,
        choices=[m.value for m in ScanMode],
        default="standard",
        help="Scanner mode (default: standard)"
    )
    
    # Basic configuration
    parser.add_argument(
        "--location", "-l",
        type=str,
        default=os.getenv("SCANNER_LOCATION", "default-location"),
        help="Scanner location identifier"
    )
    
    parser.add_argument(
        "--producer-id", "-p",
        type=str,
        default=os.getenv("PRODUCER_ID", "beacon-scanner-01"),
        help="Unique producer ID for this scanner"
    )
    
    # API configuration
    parser.add_argument(
        "--api-url",
        type=str,
        default=os.getenv("SPECS_API_URL", "http://localhost:8001"),
        help="SPECS Form API URL"
    )
    
    parser.add_argument(
        "--api-key",
        type=str,
        default=os.getenv("SPECS_API_KEY", "sk_prod_7K9mXvN2pQ5rT8wY3hL6jF4aB1cD"),
        help="API authentication key"
    )
    
    # Scan parameters
    parser.add_argument(
        "--scan-interval",
        type=int,
        default=30,
        help="Seconds between scans (default: 30)"
    )
    
    parser.add_argument(
        "--scan-duration",
        type=int,
        default=10,
        help="Seconds per scan (default: 10)"
    )
    
    # Filtering options
    parser.add_argument(
        "--rssi-threshold",
        type=float,
        default=-90.0,
        help="Minimum RSSI to consider (default: -90)"
    )
    
    parser.add_argument(
        "--no-filtering",
        action="store_true",
        help="Disable enhanced filtering"
    )
    
    # Batch mode options
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Detections per batch (default: 50)"
    )
    
    parser.add_argument(
        "--batch-interval",
        type=int,
        default=300,
        help="Seconds between batch submissions (default: 300)"
    )
    
    # Beacon mappings
    parser.add_argument(
        "--mappings",
        type=str,
        help="Path to JSON file with beacon MAC to memorable ID mappings"
    )
    
    # Other options
    parser.add_argument(
        "--mock-beacons",
        action="store_true",
        help="Use mock beacons instead of real BLE scanning"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without submitting to API"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load beacon mappings if provided
    beacon_mappings = {}
    if args.mappings:
        beacon_mappings = load_beacon_mappings(args.mappings)
        logger.info(f"Loaded {len(beacon_mappings)} beacon mappings")
    
    # Create configuration
    config = ScannerConfig(
        api_url=args.api_url,
        api_key=args.api_key,
        mode=ScanMode(args.mode),
        location=args.location,
        producer_id=args.producer_id,
        scan_interval=args.scan_interval,
        scan_duration=args.scan_duration,
        rssi_threshold=args.rssi_threshold,
        enable_filtering=not args.no_filtering,
        batch_size=args.batch_size,
        batch_interval=args.batch_interval,
        beacon_mappings=beacon_mappings,
        mock_beacons=args.mock_beacons,
        dry_run=args.dry_run
    )
    
    # Create and run scanner
    scanner = BeaconScanner(config)
    
    try:
        asyncio.run(scanner.run())
    except KeyboardInterrupt:
        logger.info("\nScanner stopped.")


if __name__ == "__main__":
    main()