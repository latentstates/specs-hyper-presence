# Beacon Scanner & SPECS Form API Integration Guide

This guide demonstrates how to integrate ESP32-C3 BLE beacons with the SPECS Form External Data API for participant tracking in experiments.

## Overview

The integration consists of three main components:

1. **ESP32-C3 Beacons** - Wearable devices that broadcast BLE advertisements
2. **Beacon Scanner** - Python application that detects beacons and determines location
3. **SPECS Form API** - Backend system that stores and manages experiment data

```
┌─────────────┐     BLE      ┌──────────────┐    HTTP    ┌─────────────┐
│   ESP32-C3  │ ─────────────>│    Scanner   │ ──────────>│ SPECS Form  │
│   Beacon    │  Advertisement│   (Python)   │    API     │     API     │
└─────────────┘     30s       └──────────────┘            └─────────────┘
```

## Quick Start

### 1. Install Dependencies

```bash
# Clone the repository
git clone https://github.com/latentstates/specs-hyper-presence.git
cd specs-hyper-presence

# Option 1: Install minimal requirements
pip install -r requirements-minimal.txt

# Option 2: Install all requirements (includes dev tools)
pip install -r requirements.txt

# Option 3: Install as a package
pip install -e .  # Basic installation
pip install -e ".[enhanced]"  # With enhanced scanner features
pip install -e ".[dev]"  # With development tools
```

### 2. Basic Usage

```bash
# Simple mode (no hardware required, uses mock data)
python beacon_scanner/beacon_scanner.py --mode simple --location entrance

# Production mode (requires BLE hardware and sudo on macOS/Linux)
sudo python beacon_scanner/beacon_scanner.py --mode standard --location lab-room-a
```

### 3. Create Beacon Mappings

Create a file `beacon_mappings.json` that maps beacon MAC addresses to participants:

```json
{
    "AA:BB:CC:DD:EE:01": "soft-plum-snake",
    "AA:BB:CC:DD:EE:02": "brave-amber-lynx",
    "AA:BB:CC:DD:EE:03": "quick-jade-fox"
}
```

Use it with:
```bash
sudo python beacon_scanner/beacon_scanner.py --mappings beacon_mappings.json
```

## Integration Examples

### Example 1: Basic Scanner Setup

```python
#!/usr/bin/env python3
"""
Basic beacon scanner integration example
"""
import sys
import os

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from beacon_scanner import BeaconScanner, ScannerConfig, ScanMode
from specs_client.client import create_client

# Configure the scanner
config = ScannerConfig(
    api_url="http://localhost:8001",
    api_key="your-api-key",
    mode=ScanMode.STANDARD,
    location="entrance",
    producer_id="scanner-01",
    scan_interval=30,  # seconds
    scan_duration=10,  # seconds
    beacon_mappings={
        "AA:BB:CC:DD:EE:01": "soft-plum-snake",
        "AA:BB:CC:DD:EE:02": "brave-amber-lynx"
    }
)

# Create and run scanner
scanner = BeaconScanner(config)

# Run the scanner (this blocks)
import asyncio
asyncio.run(scanner.run())
```

### Example 2: Custom Detection Handler

```python
"""
Custom beacon detection processing
"""
from beacon_scanner import BeaconScanner, ScannerConfig, ScanMode, BeaconDetection
from specs_client.client import create_client, submit_beacon_detection
from typing import List
import asyncio

class CustomBeaconScanner(BeaconScanner):
    """Extended scanner with custom detection handling"""
    
    async def process_detection(self, detection: BeaconDetection) -> bool:
        """Custom processing for each detection"""
        
        # Add custom logic here
        print(f"🎯 Detected {detection.mac_address} at {detection.scanner_location}")
        print(f"   RSSI: {detection.rssi} dBm")
        print(f"   Participant: {detection.memorable_id}")
        
        # Calculate proximity
        if detection.rssi > -50:
            proximity = "very close"
        elif detection.rssi > -70:
            proximity = "nearby"
        else:
            proximity = "far"
        
        print(f"   Proximity: {proximity}")
        
        # Call parent method to submit to API
        return await self.submit_detection(detection)
    
    async def run_scan_cycle(self) -> int:
        """Override to add custom processing"""
        detections = await self.get_detections()
        
        # Custom filtering based on signal strength patterns
        filtered_detections = []
        for d in detections:
            # Only include strong signals in certain locations
            if self.config.location == "entrance" and d.rssi < -70:
                continue
            filtered_detections.append(d)
        
        # Process each detection
        success_count = 0
        for detection in filtered_detections:
            if await self.process_detection(detection):
                success_count += 1
        
        return success_count

# Use the custom scanner
config = ScannerConfig(
    mode=ScanMode.STANDARD,
    location="entrance",
    scan_interval=20
)

scanner = CustomBeaconScanner(config)
asyncio.run(scanner.run())
```

### Example 3: Multi-Location Deployment

```python
"""
Deploy multiple scanners for complete facility coverage
"""
import asyncio
import multiprocessing
from beacon_scanner import BeaconScanner, ScannerConfig, ScanMode

def run_scanner(location: str, producer_id: str):
    """Run a scanner instance for a specific location"""
    config = ScannerConfig(
        mode=ScanMode.STANDARD,
        location=location,
        producer_id=producer_id,
        scan_interval=30,
        beacon_mappings=load_beacon_mappings("beacon_mappings.json")
    )
    
    scanner = BeaconScanner(config)
    asyncio.run(scanner.run())

def deploy_multi_location():
    """Deploy scanners at multiple locations"""
    locations = [
        ("entrance", "scanner-01"),
        ("lab-room-a", "scanner-02"),
        ("lab-room-b", "scanner-03"),
        ("hallway", "scanner-04"),
        ("exit", "scanner-05")
    ]
    
    processes = []
    
    for location, producer_id in locations:
        p = multiprocessing.Process(
            target=run_scanner,
            args=(location, producer_id)
        )
        p.start()
        processes.append(p)
        print(f"Started scanner at {location}")
    
    # Wait for all processes
    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        print("\nStopping all scanners...")
        for p in processes:
            p.terminate()

if __name__ == "__main__":
    deploy_multi_location()
```

### Example 4: Direct API Integration

```python
"""
Direct SPECS Form API usage without the scanner
"""
from specs_client.client import create_client, submit_beacon_detection

# Create API client
client = create_client(
    base_url="http://localhost:8001",
    api_key="your-api-key"
)

# Lookup participant by memorable ID
participant = client.lookup_participant(memorable_id="soft-plum-snake")
if participant:
    participant_id = participant["participant_id"]
    
    # Submit a beacon detection
    success = submit_beacon_detection(
        client=client,
        participant_id=participant_id,
        location="entrance",
        mac_address="AA:BB:CC:DD:EE:01",
        rssi=-55.0,
        producer_id="manual-test"
    )
    
    if success:
        print("✅ Detection submitted successfully")
else:
    print("❌ Participant not found")

# Get all detections for a participant
detections = client.get_participant_data(
    participant_id=participant_id,
    data_type="beacon_detection"
)

for detection in detections:
    print(f"Location: {detection['data']['scanner_location']}")
    print(f"Time: {detection['timestamp']}")
    print(f"RSSI: {detection['data']['rssi']}")
```

### Example 5: Batch Processing Mode

```python
"""
Efficient batch processing for high-volume deployments
"""
from beacon_scanner import BeaconScanner, ScannerConfig, ScanMode
from datetime import datetime, timedelta
import asyncio

# Configure for batch mode
config = ScannerConfig(
    mode=ScanMode.BATCH,
    location="high-traffic-area",
    producer_id="batch-scanner-01",
    batch_size=100,        # Submit every 100 detections
    batch_interval=300,    # Or every 5 minutes
    scan_interval=10,      # Scan every 10 seconds
    scan_duration=5        # Quick 5-second scans
)

# The scanner will automatically batch detections
scanner = BeaconScanner(config)

# Add monitoring
async def monitor_scanner():
    """Monitor scanner statistics"""
    scanner = BeaconScanner(config)
    
    # Start scanner in background
    scanner_task = asyncio.create_task(scanner.run())
    
    # Monitor loop
    while True:
        await asyncio.sleep(60)  # Check every minute
        
        print(f"\n📊 Scanner Statistics at {datetime.now():%H:%M:%S}")
        print(f"Cached detections: {len(scanner.detection_cache)}")
        print(f"Unique beacons seen: {len(scanner.seen_beacons)}")
        print(f"Known participants: {len(scanner.participant_cache)}")

# Run with monitoring
asyncio.run(monitor_scanner())
```

## Configuration Options

### Environment Variables

```bash
# API Configuration
export SPECS_API_URL="http://localhost:8001"
export SPECS_API_KEY="sk_prod_your_api_key"

# Scanner Configuration
export SCANNER_LOCATION="entrance"
export PRODUCER_ID="beacon-scanner-01"

# Run scanner with environment config
sudo python beacon_scanner/beacon_scanner.py
```

### Command Line Arguments

```bash
# Full configuration via CLI
sudo python beacon_scanner/beacon_scanner.py \
    --mode enhanced \
    --location "conference-room" \
    --producer-id "scanner-conf-01" \
    --api-url "https://api.specsform.com" \
    --api-key "sk_prod_your_key" \
    --scan-interval 20 \
    --scan-duration 15 \
    --rssi-threshold -70 \
    --batch-size 50 \
    --mappings beacon_mappings.json \
    --verbose
```

### Configuration File

Create `scanner_config.json`:

```json
{
    "api_url": "http://localhost:8001",
    "api_key": "sk_prod_your_key",
    "scanners": [
        {
            "location": "entrance",
            "producer_id": "scanner-01",
            "mode": "standard",
            "scan_interval": 30
        },
        {
            "location": "lab-room-a",
            "producer_id": "scanner-02",
            "mode": "enhanced",
            "scan_interval": 20,
            "rssi_threshold": -60
        }
    ]
}
```

## Data Flow

### 1. Beacon Detection

```python
# When a beacon is detected, the scanner creates:
detection = BeaconDetection(
    mac_address="AA:BB:CC:DD:EE:01",
    rssi=-55.0,
    timestamp=datetime.now(),
    scanner_location="entrance",
    memorable_id="soft-plum-snake",  # From mappings
    participant_id=None  # Looked up from API
)
```

### 2. Participant Lookup

```python
# The scanner automatically looks up participants:
participant = client.lookup_participant(memorable_id="soft-plum-snake")
# Returns: {"participant_id": "uuid", "experiment_id": "uuid", ...}
```

### 3. Data Submission

```python
# Detection data is submitted as:
{
    "producer_id": "scanner-01",
    "event_type": "beacon_detection",
    "timestamp": "2024-01-19T14:30:22Z",
    "data": {
        "scanner_location": "entrance",
        "beacon_mac": "AA:BB:CC:DD:EE:01",
        "rssi": -55.0,
        "signal_quality": "good"
    }
}
```

### 4. Data Retrieval

```python
# Retrieve detection history:
detections = client.get_participant_data(
    participant_id="participant-uuid",
    data_type="beacon_detection",
    start_time=datetime.now() - timedelta(hours=1),
    end_time=datetime.now()
)

# Process location history
locations = []
for d in detections:
    locations.append({
        "time": d["timestamp"],
        "location": d["data"]["scanner_location"],
        "rssi": d["data"]["rssi"]
    })
```

## Testing

### 1. Test Without Hardware

```bash
# Use simple mode with mock beacons
python beacon_scanner/beacon_scanner.py --mode simple --dry-run

# This generates fake beacon detections for testing
```

### 2. Test API Connection

```python
from specsform_api.client import create_client

client = create_client()
if client.health_check():
    print("✅ API connection successful")
    
    projects = client.list_projects()
    print(f"Available projects: {len(projects)}")
else:
    print("❌ API connection failed")
```

### 3. Test Beacon Detection

```bash
# Scan for real beacons without submitting
sudo python beacon_scanner/beacon_scanner.py \
    --mode standard \
    --dry-run \
    --verbose \
    --scan-duration 20
```

## Troubleshooting

### macOS Specific Issues

1. **Bluetooth Permission Denied**
   ```bash
   # Grant permission in System Preferences > Security & Privacy > Bluetooth
   # Or reset permissions:
   tccutil reset Bluetooth
   ```

2. **Multiple Scanners Conflict**
   ```bash
   # Use different scan intervals
   --scan-interval 30  # Scanner 1
   --scan-interval 35  # Scanner 2
   ```

3. **Can't Find Beacons**
   ```bash
   # Check Bluetooth is on
   system_profiler SPBluetoothDataType
   
   # Test with Bluetooth Explorer or LightBlue app
   ```

### API Issues

1. **Connection Refused**
   ```python
   # Check API is running
   curl http://localhost:8001/health
   
   # Use correct URL
   --api-url http://localhost:8001
   ```

2. **Authentication Failed**
   ```bash
   # Verify API key
   export SPECS_API_KEY="sk_prod_correct_key"
   ```

3. **Participant Not Found**
   ```python
   # List all participants
   participants = client.list_participants()
   for p in participants:
       print(f"{p['memorable_id']} -> {p['participant_id']}")
   ```

## Best Practices

1. **Beacon Management**
   - Keep beacon mappings file updated
   - Monitor battery levels (3.0V minimum)
   - Test beacons before deployment

2. **Scanner Deployment**
   - Use unique producer IDs
   - Place scanners at choke points
   - Avoid metal enclosures

3. **Data Quality**
   - Use enhanced mode for research
   - Set appropriate RSSI thresholds
   - Regular validation checks

4. **Performance**
   - Use batch mode for high traffic
   - Optimize scan intervals
   - Monitor CPU and memory usage

## Advanced Topics

### Custom Data Fields

```python
# Extend the beacon detection data
detection_data = {
    "scanner_location": location,
    "beacon_mac": mac_address,
    "rssi": rssi,
    "signal_quality": quality,
    # Add custom fields
    "temperature": 22.5,
    "humidity": 45.0,
    "battery_level": 3.2
}

client.submit_data(
    producer_id=producer_id,
    event_type="beacon_detection_extended",
    data=detection_data
)
```

### Real-time Processing

```python
# Process detections in real-time
async def process_stream():
    async for detection in scanner.detection_stream():
        # Real-time processing
        if detection.rssi > -50:
            await alert_close_proximity(detection)
        
        # Update dashboard
        await update_location_dashboard(detection)
```

### Integration with Other Systems

```python
# Export to external systems
import requests

def export_to_external_system(detection):
    payload = {
        "device_id": detection.mac_address,
        "location": detection.scanner_location,
        "timestamp": detection.timestamp.isoformat(),
        "signal_strength": detection.rssi
    }
    
    response = requests.post(
        "https://external-system.com/api/tracking",
        json=payload,
        headers={"Authorization": "Bearer token"}
    )
    
    return response.status_code == 200
```

## Support

- **Documentation**: See `/beacon_scanner/SCANNER_GUIDE.md` for detailed scanner documentation
- **API Reference**: See `/specs_client/README.md` for API client documentation
- **Hardware Setup**: See `/README.md` for ESP32-C3 beacon setup instructions

## License

This integration is part of the specs-hyper-presence project. See LICENSE file for details.