#!/usr/bin/env python3
"""
SPECS Form External Data API Client

A Python client for interacting with the SPECS Form External Data API.
Handles authentication, data submission, and participant lookup.
"""
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import requests
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class ExperimentData:
    """Data structure for experiment submission"""
    external_id: str
    participant_id: str
    experiment_type: str
    experiment_date: str
    summary_data: Dict[str, Any]
    source_system: Optional[str] = None
    quality_score: Optional[float] = None
    raw_data_url: Optional[str] = None
    project_id: Optional[str] = None
    session_id: Optional[str] = None
    data_version: Optional[str] = None
    extra_json: Optional[Dict[str, Any]] = None


class SPECSFormClient:
    """Client for SPECS Form External Data API"""
    
    def __init__(self, api_url: str = "http://localhost:8001", api_key: str = None):
        """
        Initialize the SPECS Form API client.
        
        Args:
            api_url: Base URL of the API server
            api_key: API authentication key
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
        self._session = requests.Session()
        self._session.headers.update(self.headers)
    
    def health_check(self) -> bool:
        """Check if the API server is healthy"""
        try:
            response = self._session.get(f"{self.api_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def lookup_participant(self, memorable_id: str = None, email: str = None, 
                         external_id: str = None) -> Optional[Dict]:
        """
        Look up a participant by various identifiers.
        
        Args:
            memorable_id: The participant's memorable ID
            email: The participant's email
            external_id: An external system's ID for the participant
            
        Returns:
            Participant data dict or None if not found
        """
        if not any([memorable_id, email, external_id]):
            raise ValueError("At least one identifier required")
        
        params = {}
        if memorable_id:
            params["memorable_id"] = memorable_id
        if email:
            params["email"] = email
        if external_id:
            params["external_id"] = external_id
        
        try:
            response = self._session.get(
                f"{self.api_url}/api/participants/lookup",
                params=params
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.info(f"Participant not found: {params}")
                return None
            else:
                logger.error(f"Participant lookup failed: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error looking up participant: {e}")
            return None
    
    def list_projects(self) -> List[Dict]:
        """Get list of available projects"""
        try:
            response = self._session.get(f"{self.api_url}/api/projects")
            
            if response.status_code == 200:
                return response.json()["projects"]
            else:
                logger.error(f"Failed to list projects: {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error listing projects: {e}")
            return []
    
    def register_producer(self, producer_id: str, name: str, producer_type: str,
                         project_id: str, organization: str = None, 
                         version: str = None, config: Dict = None) -> bool:
        """
        Register a data producer.
        
        Args:
            producer_id: Unique identifier for the producer
            name: Human-readable name
            producer_type: Type of producer (e.g., "beacon_scanner")
            project_id: Default project for this producer's data
            organization: Organization name
            version: Producer version
            config: Additional configuration as dict
            
        Returns:
            True if successful, False otherwise
        """
        data = {
            "producer_id": producer_id,
            "name": name,
            "producer_type": producer_type,
            "project_id": project_id
        }
        
        if organization:
            data["organization"] = organization
        if version:
            data["version"] = version
        if config:
            data["config_json"] = config
        
        try:
            response = self._session.post(
                f"{self.api_url}/api/producers/register",
                json=data
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Registered producer: {producer_id}")
                return True
            elif response.status_code == 409 or "already" in response.text.lower():
                logger.info(f"Producer already registered: {producer_id}")
                return True
            else:
                logger.error(f"Failed to register producer: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error registering producer: {e}")
            return False
    
    def submit_experiment(self, data: ExperimentData) -> Optional[Dict]:
        """
        Submit experiment data.
        
        Args:
            data: ExperimentData object with experiment details
            
        Returns:
            Response dict with submission details or None if failed
        """
        # Convert dataclass to dict, removing None values
        submission_data = {k: v for k, v in asdict(data).items() if v is not None}
        
        try:
            response = self._session.post(
                f"{self.api_url}/api/experiments/submit",
                json=submission_data
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(f"Submitted experiment: {data.external_id}")
                return result
            else:
                logger.error(f"Failed to submit experiment: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error submitting experiment: {e}")
            return None
    
    def query_experiments(self, participant_id: str = None, project_id: str = None,
                         experiment_type: str = None, limit: int = 100) -> List[Dict]:
        """
        Query submitted experiments.
        
        Args:
            participant_id: Filter by participant
            project_id: Filter by project
            experiment_type: Filter by experiment type
            limit: Maximum number of results
            
        Returns:
            List of experiment data dicts
        """
        params = {"limit": limit}
        if participant_id:
            params["participant_id"] = participant_id
        if project_id:
            params["project_id"] = project_id
        if experiment_type:
            params["experiment_type"] = experiment_type
        
        try:
            response = self._session.get(
                f"{self.api_url}/api/experiments/query",
                params=params
            )
            
            if response.status_code == 200:
                return response.json()["data"]
            else:
                logger.error(f"Failed to query experiments: {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error querying experiments: {e}")
            return []
    
    def get_participant_experiments(self, participant_id: str, 
                                  experiment_type: str = None) -> List[Dict]:
        """
        Get all experiments for a specific participant.
        
        Args:
            participant_id: The participant's UUID
            experiment_type: Optional filter by experiment type
            
        Returns:
            List of experiment data dicts
        """
        params = {}
        if experiment_type:
            params["experiment_type"] = experiment_type
        
        try:
            response = self._session.get(
                f"{self.api_url}/api/participants/{participant_id}/experiments",
                params=params
            )
            
            if response.status_code == 200:
                return response.json()["experiments"]
            else:
                logger.error(f"Failed to get participant experiments: {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting participant experiments: {e}")
            return []
    
    def close(self):
        """Close the client session"""
        self._session.close()
    
    def __enter__(self):
        """Context manager support"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        self.close()


# Convenience functions
def create_client(api_url: str = "http://localhost:8001", 
                 api_key: str = "sk_prod_7K9mXvN2pQ5rT8wY3hL6jF4aB1cD") -> SPECSFormClient:
    """Create a SPECS Form API client with default settings"""
    return SPECSFormClient(api_url, api_key)


def submit_beacon_detection(client: SPECSFormClient, participant_id: str, 
                          location: str, mac_address: str, rssi: float,
                          producer_id: str = "beacon-scanner") -> bool:
    """
    Submit a beacon detection to SPECS Form.
    
    Args:
        client: SPECSFormClient instance
        participant_id: UUID of the participant
        location: Scanner location
        mac_address: Beacon MAC address
        rssi: Signal strength
        producer_id: ID of the scanner/producer
        
    Returns:
        True if successful, False otherwise
    """
    data = ExperimentData(
        external_id=f"BEACON-{location}-{datetime.now():%Y%m%d-%H%M%S}-{mac_address.replace(':', '')}",
        participant_id=participant_id,
        experiment_type="beacon_tracking",
        experiment_date=datetime.now().isoformat(),
        source_system=producer_id,
        quality_score=calculate_quality_score(rssi),
        summary_data={
            "scanner_location": location,
            "beacon_mac": mac_address,
            "rssi": rssi,
            "signal_quality": get_signal_quality(rssi),
            "detection_timestamp": datetime.now().isoformat()
        }
    )
    
    result = client.submit_experiment(data)
    return result is not None


def calculate_quality_score(rssi: float) -> float:
    """Calculate quality score from RSSI (0.0 to 1.0)"""
    # Normalize RSSI (-30 best, -90 worst)
    score = (rssi + 90) / 60
    return max(0.0, min(1.0, round(score, 2)))


def get_signal_quality(rssi: float) -> str:
    """Categorize signal quality based on RSSI"""
    if rssi >= -50:
        return "excellent"
    elif rssi >= -60:
        return "good"
    elif rssi >= -70:
        return "fair"
    else:
        return "poor"