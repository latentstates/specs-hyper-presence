#!/usr/bin/env python3
"""
Test API connection and available participants
"""
import requests
import json

API_URL = "http://localhost:8001"
API_KEY = "sk_prod_7K9mXvN2pQ5rT8wY3hL6jF4aB1cD"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

print("Testing SPECS Form External Data API")
print("=" * 60)

# Test 1: Health check
print("\n1. Testing health endpoint...")
try:
    response = requests.get(f"{API_URL}/health")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   Response: {response.json()}")
    else:
        print(f"   Error: {response.text}")
except Exception as e:
    print(f"   Error: {e}")

# Test 2: List projects
print("\n2. Listing available projects...")
try:
    response = requests.get(f"{API_URL}/api/projects", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        projects = response.json()["projects"]
        print(f"   Found {len(projects)} projects:")
        for p in projects:
            print(f"   - {p['display_name']} (ID: {p['id']})")
    else:
        print(f"   Error: {response.text}")
except Exception as e:
    print(f"   Error: {e}")

# Test 3: Try different participant IDs
print("\n3. Testing participant lookup...")
test_ids = ["soft-plum-snake", "steve", "brave-amber-lynx", "test"]

for memorable_id in test_ids:
    try:
        response = requests.get(
            f"{API_URL}/api/participants/lookup",
            headers=headers,
            params={"memorable_id": memorable_id}
        )
        print(f"\n   Trying '{memorable_id}':")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Found! ID: {data.get('participant_id', 'N/A')}")
        else:
            print(f"   ❌ Not found or error: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
print("\nNote: If participant lookup fails, the database may need to be initialized")
print("or test participants may need to be created.")