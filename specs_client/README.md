# SPECS Form API Client

Python client library for the SPECS Form External Data API. This module provides a clean interface for submitting experiment data, managing data producers, and querying participant information.

Part of the [specs-hyper-presence](https://github.com/latentstates/specs-hyper-presence) project.

## Installation

```bash
# From the project root directory
pip install -r requirements-minimal.txt

# Or install the package
pip install -e .
```

## Quick Start

```python
from specs_client.client import create_client, submit_beacon_detection

# Create client
client = create_client(api_url="http://localhost:8001")

# Look up participant
participant = client.lookup_participant(memorable_id="soft-plum-snake")

# Submit beacon detection
success = submit_beacon_detection(
    client=client,
    participant_id=participant['participant_id'],
    location="entrance",
    mac_address="AA:BB:CC:DD:EE:FF",
    rssi=-55.5
)
```

## Features

- Simple, pythonic API client
- Automatic authentication handling
- Data validation with dataclasses
- Convenience functions for common operations
- Context manager support
- Comprehensive error handling

## API Methods

### Client Initialization
```python
client = SPECSFormClient(
    api_url="http://localhost:8001",
    api_key="your-api-key"
)
```

### Core Methods

- `health_check()` - Check API server status
- `lookup_participant()` - Find participant by ID
- `list_projects()` - Get available projects
- `register_producer()` - Register data producer
- `submit_experiment()` - Submit experiment data
- `query_experiments()` - Query submitted data
- `get_participant_experiments()` - Get participant's experiments

## Examples

See the `examples/` directory for complete examples:
- `submit_beacon_data.py` - Submit beacon tracking data

## Testing

Run the API connection test:
```bash
python tests/test_api_connection.py
```

## Simulator

The `simulator/` directory contains a beacon simulator for testing the integration without physical hardware:
```bash
python simulator/beacon_simulator.py 10  # Run for 10 minutes
```

## External Data API Integration

### Data Producer Registration

The API uses a hierarchical model where data producers must register before submitting data:

```python
# Register your scanner/system as a data producer
client.register_producer(
    producer_id="beacon-scanner-01",
    name="Entrance Scanner",
    producer_type="beacon_scanner",
    project_id="your-project-id",
    organization="Research Lab"
)
```

### Data Submission Flow

1. **Producer Registration** (one-time setup)
   - Each scanner/system registers as a producer
   - Associates with a default project
   - All subsequent data automatically linked to project

2. **Participant Lookup**
   - Find participant by memorable ID
   - Get participant UUID for data submission

3. **Data Submission**
   - Include `source_system` (producer ID)
   - Data automatically assigned to producer's project
   - Optional quality score and metadata

### Data Model

The API uses a three-tier hierarchy:
- **DataProducer** - The scanner or system submitting data
- **DataEvent** - Batch of related submissions
- **ExternalExperimentData** - Individual data records

### API Endpoints

- `GET /health` - Server health check
- `GET /api/participants/lookup` - Find participant by ID
- `GET /api/projects` - List available projects
- `POST /api/producers/register` - Register data producer
- `POST /api/experiments/submit` - Submit experiment data
- `GET /api/experiments/query` - Query submitted data
- `GET /api/participants/{id}/experiments` - Get participant's data

### Authentication

All API requests require authentication:
```python
headers = {
    "X-API-Key": "your-api-key",
    "Content-Type": "application/json"
}
```

Default development key: `sk_prod_7K9mXvN2pQ5rT8wY3hL6jF4aB1cD`

### Error Handling

The client provides comprehensive error handling:
- Connection errors return `None` or empty lists
- HTTP errors are logged with details
- Validation errors prevented by dataclasses
- Automatic retry logic (configurable)