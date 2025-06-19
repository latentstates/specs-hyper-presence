# Beacon Scanner

Unified BLE beacon scanner for tracking ESP32-C3 beacons with SPECS Form integration.

Part of the [specs-hyper-presence](https://github.com/latentstates/specs-hyper-presence) project.

## Features

- **Multiple modes**: Simple (mock), Standard, Enhanced, and Batch
- **CLI interface**: Full command-line control
- **Flexible configuration**: Environment variables or command-line arguments
- **Quality filtering**: RSSI thresholds and signal quality metrics
- **Batch processing**: Efficient bulk data submission
- **Offline support**: Caching for network interruptions
- **Dry run mode**: Test without API submission

## Installation

```bash
# From the project root directory

# Option 1: Minimal installation
pip install -r requirements-minimal.txt

# Option 2: Full installation with all features
pip install -r requirements.txt

# Option 3: Install as editable package
pip install -e .
```

## Quick Start

```bash
# Simple mode (no BLE required, mock data)
python beacon_scanner.py --mode simple --location entrance

# Standard BLE scanning
sudo python beacon_scanner.py --mode standard --location lab-room-a

# Enhanced mode with quality filtering
sudo python beacon_scanner.py --mode enhanced --rssi-threshold -70

# Batch mode for efficiency
sudo python beacon_scanner.py --mode batch --batch-size 100
```

## Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `simple` | Mock data generation | Testing, development |
| `standard` | Basic BLE scanning | Production deployment |
| `enhanced` | Advanced filtering | Research, high accuracy |
| `batch` | Delayed submission | High-volume, efficiency |

## Configuration

### Command Line Options

```bash
python beacon_scanner.py --help
```

Key options:
- `--mode`: Scanner operational mode
- `--location`: Physical location identifier
- `--producer-id`: Unique scanner ID
- `--scan-interval`: Seconds between scans
- `--scan-duration`: Seconds per scan
- `--rssi-threshold`: Minimum signal strength
- `--batch-size`: Detections per batch
- `--mappings`: Beacon to participant mappings file
- `--dry-run`: Test without API submission

### Environment Variables

```bash
export SPECS_API_URL="http://localhost:8001"
export SPECS_API_KEY="your-api-key"
export SCANNER_LOCATION="entrance"
export PRODUCER_ID="beacon-scanner-01"
```

### Beacon Mappings

Create a JSON file mapping MAC addresses to participant memorable IDs:

```json
{
    "AA:BB:CC:DD:EE:01": "soft-plum-snake",
    "AA:BB:CC:DD:EE:02": "brave-amber-lynx"
}
```

Use with: `--mappings beacon_mappings.json`

## Examples

### Development Testing
```bash
# Mock beacons, no BLE required
python beacon_scanner.py --mode simple --dry-run
```

### Production Deployment
```bash
# Standard scanning with mappings
sudo python beacon_scanner.py \
    --mode standard \
    --location entrance \
    --mappings beacon_mappings.json \
    --scan-interval 30
```

### Research Configuration
```bash
# Enhanced mode with strict filtering
sudo python beacon_scanner.py \
    --mode enhanced \
    --location lab-room-a \
    --rssi-threshold -60 \
    --scan-duration 20
```

### High-Volume Deployment
```bash
# Batch mode for multiple scanners
sudo python beacon_scanner.py \
    --mode batch \
    --batch-size 200 \
    --batch-interval 600 \
    --location hallway
```

## Output

The scanner provides real-time feedback:

```
🔵 Beacon Scanner Starting
============================================================
Location: entrance
Producer ID: beacon-scanner-01
Scan interval: 30s
------------------------------------------------------------

🔍 Scan #1 at 14:30:22
Detected 3 beacons
✅ Submitted 3 detections
📊 Unique beacons seen: 3
📤 Total submitted: 3
```

## Troubleshooting

### Permission Denied
```bash
# Linux/Mac
sudo python beacon_scanner.py

# Or add user to bluetooth group
sudo usermod -a -G bluetooth $USER
```

### No Beacons Detected
- Check beacon batteries
- Verify Bluetooth enabled: `hciconfig hci0 up`
- Try `--mock-beacons` flag for testing
- Increase `--scan-duration`

### API Connection Failed
- Verify SPECS Form API is running
- Check `--api-url` setting
- Use `--dry-run` for offline testing

## Documentation

See `SCANNER_GUIDE.md` for detailed deployment and operational guidance.

## Legacy Scripts

The following scripts have been consolidated into `beacon_scanner.py`:
- `beacon_scanner_simple.py` → Use `--mode simple`
- `beacon_scanner_latest.py` → Use `--mode standard`
- `beacon_scanner_enhanced.py` → Use `--mode enhanced`
- `beacon_scanner_server.py` → Use `--mode batch`