#!/usr/bin/env python3
"""
Beacon Simulator for SPECS Form External Data API v3
Updated to use the correct test participant 'soft-plum-snake' and follow current API workflow
"""
import asyncio
import json
import logging
import os
import random
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import requests
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
API_URL = os.getenv("SPECS_API_URL", "http://localhost:8001")
API_KEY = os.getenv("SPECS_API_KEY", "sk_prod_7K9mXvN2pQ5rT8wY3hL6jF4aB1cD")
TEST_PARTICIPANT = "soft-plum-snake"  # Current test participant in the API

class Location(Enum):
    """Possible locations for beacons"""
    ENTRANCE = "entrance"
    LAB_ROOM_A = "lab-room-a"
    LAB_ROOM_B = "lab-room-b"
    HALLWAY = "hallway"
    CAFETERIA = "cafeteria"
    EXIT = "exit"
    OUTDOOR_AREA = "outdoor-area"

@dataclass
class SimulatedBeacon:
    """Represents a simulated beacon"""
    mac_address: str
    participant_id: str
    memorable_id: str
    current_location: Location
    last_movement: datetime
    movement_pattern: str  # "stationary", "wanderer", "scheduled"
    battery_level: float  # 0.0 to 1.0
    display_name: str  # For display purposes

@dataclass
class Scanner:
    """Represents a scanner at a specific location"""
    scanner_id: str
    location: Location
    producer_id: str
    detection_range: float  # RSSI threshold for detection
    is_registered: bool = False

class BeaconSimulator:
    """Simulates multiple beacons and scanners sending data to SPECS Form"""
    
    def __init__(self):
        self.headers = {
            "X-API-Key": API_KEY,
            "Content-Type": "application/json"
        }
        self.beacons: List[SimulatedBeacon] = []
        self.scanners: List[Scanner] = []
        self.project_id: Optional[str] = None
        self.participant_id: Optional[str] = None
        self.participant_data: Optional[dict] = None
        
    def check_api_connection(self) -> bool:
        """Check if the API server is running"""
        try:
            response = requests.get(f"{API_URL}/health", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def lookup_participant(self) -> bool:
        """Look up the test participant"""
        try:
            response = requests.get(
                f"{API_URL}/api/participants/lookup",
                headers=self.headers,
                params={"memorable_id": TEST_PARTICIPANT}
            )
            
            if response.status_code == 200:
                self.participant_data = response.json()
                self.participant_id = self.participant_data["participant_id"]
                logger.info(f"✅ Found test participant '{TEST_PARTICIPANT}'")
                logger.info(f"   ID: {self.participant_id}")
                return True
            else:
                logger.error(f"❌ Test participant '{TEST_PARTICIPANT}' not found")
                logger.info("   Please ensure the test database is loaded")
                return False
                
        except Exception as e:
            logger.error(f"Error looking up participant: {e}")
            return False
    
    def select_project(self) -> bool:
        """Select a project for the beacon data"""
        try:
            # First, get available projects
            response = requests.get(
                f"{API_URL}/api/projects",
                headers=self.headers
            )
            
            if response.status_code != 200:
                logger.error("Failed to get projects")
                return False
                
            projects = response.json()["projects"]
            
            if not projects:
                logger.error("❌ No projects found in the system")
                return False
            
            # Look for a beacon-related project first
            beacon_project = None
            for project in projects:
                if "beacon" in project.get("name", "").lower() or "beacon" in project.get("display_name", "").lower():
                    beacon_project = project
                    break
            
            # Use beacon project if found, otherwise use first available
            if beacon_project:
                self.project_id = beacon_project["id"]
                logger.info(f"✅ Using beacon project: {beacon_project['display_name']}")
            else:
                self.project_id = projects[0]["id"]
                logger.info(f"✅ Using project: {projects[0]['display_name']}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error selecting project: {e}")
            return False
    
    def register_scanner(self, scanner: Scanner) -> bool:
        """Register a scanner as a data producer"""
        try:
            producer_data = {
                "producer_id": scanner.producer_id,
                "name": f"Beacon Scanner - {scanner.location.value}",
                "producer_type": "beacon_scanner",
                "project_id": self.project_id,
                "organization": "Beacon Simulator Lab",
                "version": "3.0",
                "config_json": {
                    "location": scanner.location.value,
                    "detection_range": scanner.detection_range,
                    "simulator": True,
                    "scan_interval": 30
                }
            }
            
            response = requests.post(
                f"{API_URL}/api/producers/register",
                headers=self.headers,
                json=producer_data
            )
            
            if response.status_code in [200, 201]:
                scanner.is_registered = True
                logger.info(f"✅ Registered scanner at {scanner.location.value}")
                return True
            else:
                # Check if already registered
                if "already" in response.text.lower() or response.status_code == 409:
                    scanner.is_registered = True
                    logger.info(f"ℹ️  Scanner at {scanner.location.value} already registered")
                    return True
                else:
                    logger.error(f"Failed to register scanner at {scanner.location.value}: {response.text}")
                    return False
                
        except Exception as e:
            logger.error(f"Error registering scanner: {e}")
            return False
    
    def initialize_beacons(self):
        """Initialize simulated beacons"""
        # Create multiple beacons all assigned to our test participant
        # In a real scenario, each beacon would be assigned to different participants
        beacon_configs = [
            ("AA:BB:CC:DD:EE:01", "Test Beacon 1", "wanderer"),
            ("AA:BB:CC:DD:EE:02", "Test Beacon 2", "stationary"),
            ("AA:BB:CC:DD:EE:03", "Test Beacon 3", "scheduled"),
            ("AA:BB:CC:DD:EE:04", "Test Beacon 4", "wanderer"),
            ("AA:BB:CC:DD:EE:05", "Test Beacon 5", "stationary")
        ]
        
        initial_locations = [
            Location.ENTRANCE,
            Location.LAB_ROOM_A,
            Location.HALLWAY,
            Location.CAFETERIA,
            Location.LAB_ROOM_B
        ]
        
        for i, (mac, name, pattern) in enumerate(beacon_configs):
            beacon = SimulatedBeacon(
                mac_address=mac,
                participant_id=self.participant_id,
                memorable_id=TEST_PARTICIPANT,
                current_location=initial_locations[i],
                last_movement=datetime.now(),
                movement_pattern=pattern,
                battery_level=random.uniform(0.7, 1.0),
                display_name=name
            )
            self.beacons.append(beacon)
            logger.info(f"Initialized {name} ({mac}) at {beacon.current_location.value}")
    
    def initialize_scanners(self):
        """Initialize scanners at each location"""
        scanners_created = 0
        for location in Location:
            scanner = Scanner(
                scanner_id=f"scanner-{location.value}",
                location=location,
                producer_id=f"beacon-scanner-sim-{location.value}",
                detection_range=-70  # RSSI threshold
            )
            self.scanners.append(scanner)
            if self.register_scanner(scanner):
                scanners_created += 1
        
        logger.info(f"Initialized {scanners_created}/{len(self.scanners)} scanners successfully")
    
    def calculate_rssi(self, beacon: SimulatedBeacon, scanner: Scanner) -> Optional[float]:
        """Calculate RSSI based on beacon location relative to scanner"""
        if beacon.current_location == scanner.location:
            # Strong signal in same location
            base_rssi = random.uniform(-45, -55)
        else:
            # Check if locations are adjacent
            adjacent_map = {
                Location.ENTRANCE: [Location.HALLWAY],
                Location.HALLWAY: [Location.ENTRANCE, Location.LAB_ROOM_A, Location.LAB_ROOM_B, Location.CAFETERIA],
                Location.LAB_ROOM_A: [Location.HALLWAY],
                Location.LAB_ROOM_B: [Location.HALLWAY],
                Location.CAFETERIA: [Location.HALLWAY, Location.OUTDOOR_AREA],
                Location.OUTDOOR_AREA: [Location.CAFETERIA, Location.EXIT],
                Location.EXIT: [Location.OUTDOOR_AREA]
            }
            
            if scanner.location in adjacent_map.get(beacon.current_location, []):
                # Weak signal from adjacent location
                base_rssi = random.uniform(-65, -75)
            else:
                # Too far away
                return None
        
        # Add some noise and battery level effect
        noise = random.uniform(-5, 5)
        battery_effect = (1 - beacon.battery_level) * -10  # Weaker signal with low battery
        
        final_rssi = base_rssi + noise + battery_effect
        
        # Only detect if above threshold
        if final_rssi >= scanner.detection_range:
            return final_rssi
        return None
    
    def move_beacon(self, beacon: SimulatedBeacon):
        """Move beacon based on its movement pattern"""
        now = datetime.now()
        time_since_move = (now - beacon.last_movement).seconds
        
        if beacon.movement_pattern == "stationary":
            # Stationary beacons don't move
            return
        
        elif beacon.movement_pattern == "wanderer":
            # Move randomly every 2-5 minutes
            if time_since_move > random.randint(120, 300):
                # Get possible adjacent locations
                adjacent_map = {
                    Location.ENTRANCE: [Location.HALLWAY],
                    Location.HALLWAY: [Location.ENTRANCE, Location.LAB_ROOM_A, Location.LAB_ROOM_B, Location.CAFETERIA],
                    Location.LAB_ROOM_A: [Location.HALLWAY],
                    Location.LAB_ROOM_B: [Location.HALLWAY],
                    Location.CAFETERIA: [Location.HALLWAY, Location.OUTDOOR_AREA],
                    Location.OUTDOOR_AREA: [Location.CAFETERIA, Location.EXIT],
                    Location.EXIT: [Location.OUTDOOR_AREA]
                }
                
                possible_moves = adjacent_map.get(beacon.current_location, [])
                if possible_moves:
                    beacon.current_location = random.choice(possible_moves)
                    beacon.last_movement = now
                    logger.info(f"{beacon.display_name} moved to {beacon.current_location.value}")
        
        elif beacon.movement_pattern == "scheduled":
            # Move through locations in a scheduled pattern
            schedule = [
                Location.ENTRANCE,
                Location.HALLWAY,
                Location.LAB_ROOM_A,
                Location.HALLWAY,
                Location.CAFETERIA,
                Location.HALLWAY,
                Location.LAB_ROOM_B,
                Location.HALLWAY,
                Location.EXIT
            ]
            
            # Move every 3 minutes
            if time_since_move > 180:
                try:
                    current_index = schedule.index(beacon.current_location)
                    next_index = (current_index + 1) % len(schedule)
                    beacon.current_location = schedule[next_index]
                    beacon.last_movement = now
                    logger.info(f"{beacon.display_name} moved to {beacon.current_location.value} (scheduled)")
                except ValueError:
                    beacon.current_location = Location.ENTRANCE
                    beacon.last_movement = now
    
    def simulate_battery_drain(self, beacon: SimulatedBeacon):
        """Simulate battery drain over time"""
        # Drain ~1% per hour
        beacon.battery_level = max(0, beacon.battery_level - 0.0003)
    
    def submit_detection(self, scanner: Scanner, beacon: SimulatedBeacon, rssi: float) -> bool:
        """Submit a beacon detection to SPECS Form API"""
        try:
            quality_score = self.calculate_quality_score(rssi, beacon.battery_level)
            
            data = {
                "external_id": f"BEACON-{scanner.location.value}-{datetime.now():%Y%m%d-%H%M%S}-{beacon.mac_address.replace(':', '')}",
                "participant_id": beacon.participant_id,
                "experiment_type": "beacon_tracking",
                "experiment_date": datetime.now().isoformat(),
                "source_system": scanner.producer_id,  # Links to registered producer
                "quality_score": quality_score,
                "summary_data": {
                    "scanner_location": scanner.location.value,
                    "beacon_mac": beacon.mac_address,
                    "beacon_name": beacon.display_name,
                    "rssi": round(rssi, 1),
                    "signal_quality": self.get_signal_quality(rssi),
                    "battery_level": round(beacon.battery_level, 2),
                    "movement_pattern": beacon.movement_pattern,
                    "detection_timestamp": datetime.now().isoformat()
                },
                "extra_json": {
                    "simulator_version": "3.0",
                    "scanner_id": scanner.scanner_id,
                    "participant_memorable_id": beacon.memorable_id
                }
            }
            
            response = requests.post(
                f"{API_URL}/api/experiments/submit",
                headers=self.headers,
                json=data
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(f"✅ Detection: {beacon.display_name} at {scanner.location.value} (RSSI: {rssi:.1f} dBm)")
                return True
            else:
                logger.error(f"Failed to submit detection: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error submitting detection: {e}")
            return False
    
    def calculate_quality_score(self, rssi: float, battery_level: float) -> float:
        """Calculate quality score based on RSSI and battery"""
        # Normalize RSSI (-30 best, -90 worst)
        rssi_score = (rssi + 90) / 60
        rssi_score = max(0, min(1, rssi_score))
        
        # Combine with battery level
        quality_score = (rssi_score * 0.8) + (battery_level * 0.2)
        return round(quality_score, 2)
    
    def get_signal_quality(self, rssi: float) -> str:
        """Categorize signal quality based on RSSI"""
        if rssi >= -50:
            return "excellent"
        elif rssi >= -60:
            return "good"
        elif rssi >= -70:
            return "fair"
        else:
            return "poor"
    
    def print_summary(self):
        """Print a summary of the simulation setup"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 Simulation Configuration")
        logger.info("=" * 60)
        logger.info(f"API Server: {API_URL}")
        logger.info(f"Participant: {TEST_PARTICIPANT} ({self.participant_id[:8]}...)")
        logger.info(f"Project: {self.project_id[:8]}...")
        logger.info(f"Beacons: {len(self.beacons)}")
        logger.info(f"Scanners: {len(self.scanners)} locations")
        logger.info(f"Scan Interval: 30 seconds")
        logger.info("=" * 60)
    
    async def run_simulation(self, duration_minutes: int = 10):
        """Run the beacon simulation"""
        logger.info("=" * 60)
        logger.info("🎯 Starting Beacon Simulator v3")
        logger.info("=" * 60)
        
        # Step 1: Check API connection
        logger.info("\n1️⃣  Checking API connection...")
        if not self.check_api_connection():
            logger.error(f"❌ Cannot connect to SPECS Form API at {API_URL}")
            logger.error("   Please start the API server:")
            logger.error("   cd ~/python/specsform/features/external-data-api")
            logger.error("   ./tools/start_api_server.sh")
            return
        logger.info("✅ Connected to SPECS Form API")
        
        # Step 2: Look up participant
        logger.info("\n2️⃣  Looking up test participant...")
        if not self.lookup_participant():
            logger.error("❌ Cannot proceed without test participant")
            return
        
        # Step 3: Select project
        logger.info("\n3️⃣  Selecting project...")
        if not self.select_project():
            logger.error("❌ Cannot proceed without a project")
            return
        
        # Step 4: Initialize beacons
        logger.info("\n4️⃣  Initializing beacons...")
        self.initialize_beacons()
        
        # Step 5: Register scanners
        logger.info("\n5️⃣  Registering scanners as data producers...")
        self.initialize_scanners()
        
        # Print summary
        self.print_summary()
        
        # Start simulation
        logger.info(f"\n🚀 Starting {duration_minutes}-minute simulation...")
        logger.info("-" * 60)
        
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        scan_interval = 30  # seconds
        scan_count = 0
        
        while datetime.now() < end_time:
            scan_count += 1
            logger.info(f"\n🔍 Scan #{scan_count} at {datetime.now():%H:%M:%S}")
            
            # Move beacons
            for beacon in self.beacons:
                self.move_beacon(beacon)
                self.simulate_battery_drain(beacon)
            
            # Perform detections
            detections = 0
            submissions = 0
            
            for scanner in self.scanners:
                if not scanner.is_registered:
                    continue
                    
                for beacon in self.beacons:
                    rssi = self.calculate_rssi(beacon, scanner)
                    if rssi is not None:
                        detections += 1
                        if self.submit_detection(scanner, beacon, rssi):
                            submissions += 1
            
            logger.info(f"📊 Found {detections} detections, submitted {submissions} successfully")
            
            # Show current status
            logger.info("\n📍 Current beacon status:")
            for beacon in self.beacons:
                logger.info(f"   {beacon.display_name}: {beacon.current_location.value} "
                          f"(battery: {beacon.battery_level:.1%}, pattern: {beacon.movement_pattern})")
            
            # Calculate remaining time
            elapsed = datetime.now() - start_time
            remaining = end_time - datetime.now()
            if remaining.total_seconds() > 0:
                logger.info(f"\n⏱️  Elapsed: {elapsed.seconds//60}m {elapsed.seconds%60}s, "
                          f"Remaining: {remaining.seconds//60}m {remaining.seconds%60}s")
            
            # Wait for next scan
            if datetime.now() < end_time:
                await asyncio.sleep(scan_interval)
        
        # Simulation complete
        logger.info("\n" + "=" * 60)
        logger.info("✅ Simulation completed!")
        logger.info("=" * 60)
        logger.info(f"Duration: {duration_minutes} minutes")
        logger.info(f"Total scans: {scan_count}")
        logger.info(f"Data submitted to project: {self.project_id}")
        logger.info("\n📊 View the data in SPECS Form:")
        logger.info(f"   {API_URL.replace(':8001', ':8000')}/dashboard/external-data")
        logger.info("=" * 60)

def main():
    """Main entry point"""
    # Parse command line arguments
    duration = 10  # default duration in minutes
    
    if len(sys.argv) > 1:
        try:
            duration = int(sys.argv[1])
            if duration < 1:
                raise ValueError("Duration must be at least 1 minute")
        except ValueError as e:
            logger.error(f"Invalid duration: {e}")
            logger.info("Usage: python beacon_simulator_v3.py [duration_in_minutes]")
            logger.info("Example: python beacon_simulator_v3.py 30")
            sys.exit(1)
    
    # Create and run simulator
    simulator = BeaconSimulator()
    
    try:
        asyncio.run(simulator.run_simulation(duration))
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Simulation interrupted by user")
        logger.info("Data submitted so far has been saved to SPECS Form")

if __name__ == "__main__":
    main()