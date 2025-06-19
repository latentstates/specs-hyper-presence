#!/usr/bin/env python3
"""
Example: Submit beacon tracking data to SPECS Form

This example shows how to use the SPECS Form API client to submit
beacon detection data from a scanner.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from client import create_client, ExperimentData, submit_beacon_detection


def main():
    """Example of submitting beacon data to SPECS Form"""
    
    # Create API client
    client = create_client()
    
    print("SPECS Form Beacon Data Submission Example")
    print("=" * 50)
    
    # Check API connection
    if not client.health_check():
        print("❌ Cannot connect to API server")
        return
    
    print("✅ Connected to SPECS Form API")
    
    # Look up a participant
    participant_id = "soft-plum-snake"
    participant = client.lookup_participant(memorable_id=participant_id)
    
    if not participant:
        print(f"❌ Participant '{participant_id}' not found")
        return
    
    print(f"✅ Found participant: {participant['participant_id']}")
    
    # Register as a data producer (optional, only needed once)
    projects = client.list_projects()
    if projects:
        project_id = projects[0]["id"]
        
        registered = client.register_producer(
            producer_id="example-beacon-scanner",
            name="Example Beacon Scanner",
            producer_type="beacon_scanner",
            project_id=project_id,
            organization="Example Lab"
        )
        
        if registered:
            print("✅ Registered as data producer")
    
    # Submit a beacon detection using convenience function
    success = submit_beacon_detection(
        client=client,
        participant_id=participant['participant_id'],
        location="entrance",
        mac_address="AA:BB:CC:DD:EE:FF",
        rssi=-55.5,
        producer_id="example-beacon-scanner"
    )
    
    if success:
        print("✅ Beacon detection submitted successfully!")
    
    # Or submit manually with more control
    data = ExperimentData(
        external_id=f"BEACON-MANUAL-{datetime.now():%Y%m%d-%H%M%S}",
        participant_id=participant['participant_id'],
        experiment_type="beacon_tracking",
        experiment_date=datetime.now().isoformat(),
        source_system="example-beacon-scanner",
        quality_score=0.95,
        summary_data={
            "scanner_location": "lab-room-a",
            "beacon_mac": "11:22:33:44:55:66",
            "rssi": -48.2,
            "signal_quality": "excellent",
            "detection_timestamp": datetime.now().isoformat(),
            "custom_field": "Any additional data"
        },
        extra_json={
            "scanner_version": "1.0",
            "battery_level": 0.87
        }
    )
    
    result = client.submit_experiment(data)
    if result:
        print(f"✅ Manual submission successful! ID: {result['id']}")
    
    # Query recent submissions
    recent = client.query_experiments(
        participant_id=participant['participant_id'],
        experiment_type="beacon_tracking",
        limit=5
    )
    
    print(f"\n📊 Found {len(recent)} recent beacon detections")
    for exp in recent:
        print(f"   - {exp['external_id']} at {exp['summary_data']['scanner_location']}")
    
    # Clean up
    client.close()
    print("\n✅ Done!")


if __name__ == "__main__":
    main()