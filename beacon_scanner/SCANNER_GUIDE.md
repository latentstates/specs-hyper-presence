# Beacon Scanner Guide

Complete guide for deploying and operating the unified BLE beacon scanner with ESP32-C3 beacons.

Part of the [specs-hyper-presence](https://github.com/latentstates/specs-hyper-presence) project.

## Overview

The beacon scanner is a Python module that detects ESP32-C3 beacons worn by participants and tracks their location throughout a facility. It continuously monitors for beacon advertisements and submits detection data to SPECS Form for analysis.

## How It Works

```
ESP32 Beacon → BLE Advertisement → Scanner → SPECS Form API
    (MAC)         (Every 30s)      (Python)    (REST API)
```

1. **Beacon broadcasts** - ESP32 wakes every 30 seconds and sends BLE advertisement with MAC address
2. **Scanner detects** - Python scanner using Bleak library detects advertisements
3. **Data processing** - Scanner records MAC, RSSI signal strength, and timestamp
4. **Participant mapping** - MAC address mapped to participant memorable ID
5. **Data submission** - Detection data sent to SPECS Form API

## Scanner Modes

The unified scanner (`beacon_scanner.py`) supports four operational modes:

### Simple Mode
Testing and development without BLE hardware:
- Mock beacon data generation
- No Bluetooth adapter required
- Configurable detection patterns
- Perfect for API testing

```bash
python beacon_scanner.py --mode simple --location test-lab
```

### Standard Mode
Basic production scanning:
- Real BLE device detection
- Automatic API registration
- Immediate data submission
- Suitable for most deployments

```bash
sudo python beacon_scanner.py --mode standard --location entrance
```

### Enhanced Mode
Advanced research features:
- Signal quality filtering
- RSSI averaging for accuracy
- Detection clustering
- Quality score calculation

```bash
sudo python beacon_scanner.py --mode enhanced --rssi-threshold -60
```

### Batch Mode
High-volume efficiency:
- Accumulates detections
- Bulk submission at intervals
- Reduced API calls
- Network efficiency

```bash
sudo python beacon_scanner.py --mode batch --batch-size 100 --batch-interval 600
```

## Installation

### Prerequisites
- Python 3.8+
- Bluetooth 4.0+ adapter
- Linux/macOS/Windows (with appropriate permissions)

### Dependencies
```bash
# Core requirements
pip install bleak requests

# For enhanced scanner
pip install numpy pandas

# For server scanner  
pip install fastapi uvicorn sqlalchemy
```

### Permissions
```bash
# Linux/macOS - BLE requires elevated permissions
sudo python beacon_scanner.py

# Windows - Run as Administrator
```

## Configuration

### Command Line Interface

The scanner provides comprehensive CLI options:

```bash
python beacon_scanner.py --help
```

#### Core Options
- `--mode {simple,standard,enhanced,batch}` - Operational mode
- `--location LOCATION` - Scanner physical location
- `--producer-id ID` - Unique scanner identifier
- `--api-url URL` - SPECS Form API endpoint
- `--api-key KEY` - API authentication key

#### Scan Parameters
- `--scan-interval SECONDS` - Time between scans (default: 30)
- `--scan-duration SECONDS` - Duration of each scan (default: 10)
- `--rssi-threshold DBM` - Minimum signal strength (default: -90)
- `--no-filtering` - Disable enhanced filtering

#### Batch Options
- `--batch-size COUNT` - Detections per batch (default: 50)
- `--batch-interval SECONDS` - Time between submissions (default: 300)

#### Other Options
- `--mappings FILE` - JSON file with beacon mappings
- `--mock-beacons` - Use mock data instead of BLE
- `--dry-run` - Test without API submission
- `--verbose` - Enable debug logging

### Environment Variables

All command-line options can be set via environment:

```bash
export SPECS_API_URL="http://localhost:8001"
export SPECS_API_KEY="sk_prod_7K9mXvN2pQ5rT8wY3hL6jF4aB1cD"
export SCANNER_LOCATION="entrance"
export PRODUCER_ID="beacon-scanner-01"
```

### Beacon Mappings

Create a JSON file mapping MAC addresses to participant memorable IDs:

```json
{
    "AA:BB:CC:DD:EE:01": "soft-plum-snake",
    "AA:BB:CC:DD:EE:02": "brave-amber-lynx",
    "AA:BB:CC:DD:EE:03": "quick-jade-fox"
}
```

Use with: `--mappings beacon_mappings.json`

### Scanner Locations

Common location identifiers:
- `entrance` - Building entrance
- `exit` - Building exit
- `hallway` - Main corridor
- `lab-room-a` - Laboratory A
- `lab-room-b` - Laboratory B
- `cafeteria` - Dining area
- `outdoor-area` - Outside space

## Deployment

### Single Scanner
```bash
# Basic deployment
sudo python beacon_scanner.py --mode standard

# With specific location
sudo python beacon_scanner.py --mode standard --location entrance
```

### Multiple Scanners

Deploy scanners at multiple locations for complete coverage:

```bash
# Terminal 1 - Entrance
sudo python beacon_scanner.py --mode standard --location entrance --producer-id scanner-01

# Terminal 2 - Lab Room A  
sudo python beacon_scanner.py --mode standard --location lab-room-a --producer-id scanner-02

# Terminal 3 - Exit
sudo python beacon_scanner.py --mode standard --location exit --producer-id scanner-03
```

### Systemd Service (Linux)

Create `/etc/systemd/system/beacon-scanner.service`:
```ini
[Unit]
Description=Beacon Scanner Service
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/bin/python3 /path/to/beacon_scanner.py --mode standard --location entrance --api-url http://localhost:8001
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable beacon-scanner
sudo systemctl start beacon-scanner
```

## Data Output

Each detection creates a data record with:

```json
{
    "scanner_location": "entrance",
    "beacon_mac": "AA:BB:CC:DD:EE:01",
    "rssi": -55.4,
    "signal_quality": "good",
    "detection_timestamp": "2024-01-19T14:30:22",
    "quality_score": 0.85
}
```

### Signal Quality

RSSI (Received Signal Strength Indicator) ranges:
- `-30 to -50 dBm` - Excellent (very close)
- `-50 to -60 dBm` - Good (same room)
- `-60 to -70 dBm` - Fair (adjacent room)
- `-70 to -90 dBm` - Poor (far away)

## Troubleshooting

### No Beacons Detected
1. Check beacon batteries (should be >3.0V)
2. Verify Bluetooth is enabled: `hciconfig hci0 up`
3. Test with BLE scanner app on phone
4. Increase `SCAN_DURATION` to 20-30 seconds
5. Check beacon is in range (<10m)

### Permission Denied
```bash
# Linux - Add user to bluetooth group
sudo usermod -a -G bluetooth $USER
# Logout and login again

# Or run with sudo
sudo python beacon_scanner.py
```

### Bluetooth Adapter Issues
```bash
# Check adapter status
hciconfig -a

# Reset adapter
sudo hciconfig hci0 reset

# Check for rfkill block
rfkill list
sudo rfkill unblock bluetooth
```

### High CPU Usage
- Reduce scan duration: `--scan-duration 5`
- Increase scan interval: `--scan-interval 60`
- Use enhanced mode with filtering: `--mode enhanced`

### Intermittent Detections
- Normal behavior due to:
  - Beacon sleep cycles (30s)
  - RF interference
  - Physical obstacles
  - Battery level
- Solution: Deploy multiple scanners

## Best Practices

1. **Scanner Placement**
   - Mount at 1.5-2m height
   - Avoid metal enclosures
   - Central location in room
   - Line of sight preferred

2. **Network Reliability**
   - Use wired ethernet if possible
   - Configure local data caching
   - Implement retry logic

3. **Power Management**
   - Use powered USB hub
   - Enable auto-restart on power loss
   - Monitor scanner uptime

4. **Data Quality**
   - Regular beacon battery checks
   - Validate MAC mappings
   - Monitor quality scores
   - Check for missing data

## Maintenance

### Daily Checks
- Verify all scanners are running
- Check for detection data
- Monitor error logs

### Weekly Tasks
- Review quality scores
- Check beacon batteries
- Update participant mappings
- Clear old log files

### Monthly Tasks
- Full system test
- Update scanner software
- Replace low batteries
- Performance analysis

## Advanced Configuration

### Custom RSSI Filtering
The enhanced mode (`--mode enhanced`) automatically applies RSSI filtering and averaging:
- Groups multiple detections by MAC address
- Averages RSSI values for better accuracy
- Filters outliers and noise
- Calculates quality scores

To customize filtering behavior:
```bash
# Strict filtering with high RSSI threshold
python beacon_scanner.py --mode enhanced --rssi-threshold -60

# Disable filtering for raw data
python beacon_scanner.py --mode enhanced --no-filtering
```

### Multiple Beacon Types
```python
# Support different beacon models
BEACON_TYPES = {
    "ESP32": {"rssi_offset": 0, "tx_power": -59},
    "Nordic": {"rssi_offset": -5, "tx_power": -63},
}
```

### Location Algorithms
```python
# Triangulation with multiple scanners
def estimate_position(detections):
    # Weighted average based on RSSI
    weights = [10 ** (detection['rssi'] / 20) for detection in detections]
    # Calculate position...
```