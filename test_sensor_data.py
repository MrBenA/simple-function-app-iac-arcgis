#!/usr/bin/env python3
"""
Test script for sensor data POST endpoint
Phase 3 - Historical Data Model Testing
"""

import json
import urllib.request
import urllib.parse
from datetime import datetime

# Test endpoint URLs
# BASE_URL = "http://localhost:7071/api"  # Local testing
BASE_URL = "https://simple-func-iac-arcgis-ba.azurewebsites.net/api"  # Production

# Test data - minimal required fields
minimal_sensor_data = {
    "asset_id": "test-asset-001",
    "present_value": 5.5,
    "alarm_date": "2024-01-15T10:30:00.000Z",
    "device_type": "test sensor"
}

# Test data - complete sensor data
complete_sensor_data = {
    "location": "test-location",
    "node_id": "test-node",
    "block": "test-blk-001",
    "level": 2,
    "ward": "test-ward",
    "asset_type": "plank",
    "asset_id": "blk-001-208",
    "alarm_code": 3,
    "object_name": "early_deflection_alert",
    "description": "Early deflection alert",
    "present_value": 6.0,
    "threshold_value": 6.0,
    "min_value": -250,
    "max_value": 2,
    "resolution": 0.1,
    "units": "millimetre",
    "alarm_status": "InAlarm",
    "event_state": "HighLimit",
    "alarm_date": "2024-01-15T10:30:00.000Z",
    "device_type": "ultrasonic distance sensor"
}

def test_sensor_data_post(sensor_data, description=""):
    """Test the sensor data POST endpoint"""
    print(f"\n=== Testing Sensor Data POST: {description} ===")
    
    try:
        # Prepare POST request
        url = f"{BASE_URL}/sensor-data"
        data = json.dumps(sensor_data).encode('utf-8')
        
        request = urllib.request.Request(
            url,
            data=data,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'Python-Test-Client/1.0'
            }
        )
        
        # Make the request
        with urllib.request.urlopen(request, timeout=30) as response:
            response_data = json.loads(response.read().decode('utf-8'))
            
            print(f"✅ Status Code: {response.status}")
            print(f"✅ Response: {json.dumps(response_data, indent=2)}")
            
            if response_data.get('status') == 'success':
                return response_data.get('arcgis_objectid')
            else:
                return None
            
    except urllib.error.HTTPError as e:
        error_data = json.loads(e.read().decode('utf-8'))
        print(f"❌ HTTP Error {e.code}: {json.dumps(error_data, indent=2)}")
        return None
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def test_feature_query(asset_id):
    """Test the feature query endpoint"""
    print(f"\n=== Testing Feature Query for Asset: {asset_id} ===")
    
    try:
        url = f"{BASE_URL}/features/{asset_id}"
        
        request = urllib.request.Request(
            url,
            headers={'User-Agent': 'Python-Test-Client/1.0'}
        )
        
        with urllib.request.urlopen(request, timeout=30) as response:
            response_data = json.loads(response.read().decode('utf-8'))
            
            print(f"✅ Status Code: {response.status}")
            print(f"✅ Response: {json.dumps(response_data, indent=2)}")
            
    except urllib.error.HTTPError as e:
        error_data = json.loads(e.read().decode('utf-8'))
        print(f"❌ HTTP Error {e.code}: {json.dumps(error_data, indent=2)}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def test_health_check():
    """Test the health check endpoint"""
    print("\n=== Testing Health Check ===")
    
    try:
        url = f"{BASE_URL}/health"
        
        request = urllib.request.Request(
            url,
            headers={'User-Agent': 'Python-Test-Client/1.0'}
        )
        
        with urllib.request.urlopen(request, timeout=30) as response:
            response_data = json.loads(response.read().decode('utf-8'))
            
            print(f"✅ Status Code: {response.status}")
            print(f"✅ Health Status: {response_data.get('status')}")
            print(f"✅ ArcGIS Online: {response_data.get('dependencies', {}).get('arcgis_online')}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def main():
    """Run all tests"""
    print("🚀 Phase 3 Sensor Data Testing")
    print("=" * 50)
    
    # Test 1: Health check
    test_health_check()
    
    # Test 2: Minimal sensor data
    objectid1 = test_sensor_data_post(minimal_sensor_data, "Minimal Required Fields")
    
    # Test 3: Complete sensor data
    objectid2 = test_sensor_data_post(complete_sensor_data, "Complete Sensor Data")
    
    # Test 4: Query the data we just posted
    if objectid1:
        test_feature_query(minimal_sensor_data['asset_id'])
    
    if objectid2:
        test_feature_query(complete_sensor_data['asset_id'])
    
    # Test 5: Validation errors
    print("\n=== Testing Validation Errors ===")
    invalid_data = {"invalid": "data"}
    test_sensor_data_post(invalid_data, "Invalid Data (should fail)")
    
    print("\n✅ Testing Complete!")
    print("\nNext Steps:")
    print("1. Deploy to Azure Functions")
    print("2. Test with production URL")
    print("3. Verify records in ArcGIS Online")
    print("4. Test query endpoints")

if __name__ == "__main__":
    main()