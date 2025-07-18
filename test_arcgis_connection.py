#!/usr/bin/env python3
"""
Test script to verify ArcGIS Online connection and add test records to the hosted table.
Run this script locally before deploying to Azure Functions.
"""

import os
import json
from datetime import datetime
from arcgis.gis import GIS
from arcgis.features import FeatureLayer

# Configuration - Update these values with your actual credentials
ARCGIS_URL = "https://www.arcgis.com"
ARCGIS_USERNAME = "your-arcgis-username"  # Replace with your username
ARCGIS_PASSWORD = "your-arcgis-password"  # Replace with your password
FEATURE_SERVICE_ID = "your-feature-service-id"  # Replace with your service ID
FEATURE_LAYER_INDEX = 0  # SensorReadings table

def test_arcgis_connection():
    """Test connection to ArcGIS Online"""
    print("=" * 60)
    print("Testing ArcGIS Online Connection")
    print("=" * 60)
    
    try:
        # Connect to ArcGIS Online
        print(f"Connecting to: {ARCGIS_URL}")
        print(f"Username: {ARCGIS_USERNAME}")
        
        gis = GIS(ARCGIS_URL, ARCGIS_USERNAME, ARCGIS_PASSWORD)
        
        print(f"✅ Successfully connected!")
        print(f"   User: {gis.users.me.username}")
        print(f"   Organization: {gis.properties.name}")
        print(f"   Role: {gis.users.me.role}")
        
        return gis
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        return None

def test_feature_service_access(gis):
    """Test access to the feature service"""
    print("\n" + "=" * 60)
    print("Testing Feature Service Access")
    print("=" * 60)
    
    try:
        # Get the feature service
        print(f"Getting feature service: {FEATURE_SERVICE_ID}")
        feature_service = gis.content.get(FEATURE_SERVICE_ID)
        
        if not feature_service:
            print(f"❌ Feature service not found: {FEATURE_SERVICE_ID}")
            return None
        
        print(f"✅ Feature service found!")
        print(f"   Title: {feature_service.title}")
        print(f"   Type: {feature_service.type}")
        print(f"   Owner: {feature_service.owner}")
        
        # Get the feature layer/table
        print(f"Getting feature layer/table at index: {FEATURE_LAYER_INDEX}")
        
        # Check for both layers and tables
        layers = feature_service.layers if hasattr(feature_service, 'layers') else []
        tables = feature_service.tables if hasattr(feature_service, 'tables') else []
        
        print(f"   Available layers: {len(layers)}")
        print(f"   Available tables: {len(tables)}")
        
        # Try to get from tables first (since your service has tables)
        if tables and FEATURE_LAYER_INDEX < len(tables):
            feature_layer = tables[FEATURE_LAYER_INDEX]
            print(f"✅ Feature table found!")
            print(f"   Name: {feature_layer.properties.name}")
            print(f"   Type: {feature_layer.properties.type}")
            print(f"   URL: {feature_layer.url}")
            print(f"   Fields: {len(feature_layer.properties.fields)}")
            return feature_layer
        
        # Fall back to layers if no tables
        elif layers and FEATURE_LAYER_INDEX < len(layers):
            feature_layer = layers[FEATURE_LAYER_INDEX]
            print(f"✅ Feature layer found!")
            print(f"   Name: {feature_layer.properties.name}")
            print(f"   Type: {feature_layer.properties.type}")
            print(f"   URL: {feature_layer.url}")
            return feature_layer
        
        else:
            print("❌ No layers or tables found at the specified index")
            if not layers and not tables:
                print("   No layers or tables found in feature service")
            else:
                total_items = len(layers) + len(tables)
                print(f"   Available indices: 0 to {total_items-1}")
            return None
        
    except Exception as e:
        print(f"❌ Feature service access failed: {str(e)}")
        return None

def show_table_schema(feature_layer):
    """Show the table schema"""
    print("\n" + "=" * 60)
    print("Table Schema")
    print("=" * 60)
    
    try:
        fields = feature_layer.properties.fields
        print(f"Total fields: {len(fields)}")
        print("\nField definitions:")
        
        for field in fields:
            print(f"   {field['name']:<20} | {field['type']:<20} | {field.get('alias', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to get schema: {str(e)}")
        return False

def test_query_existing_records(feature_layer):
    """Query existing records in the table"""
    print("\n" + "=" * 60)
    print("Querying Existing Records")
    print("=" * 60)
    
    try:
        # Query all records
        result = feature_layer.query(where="1=1", return_geometry=False)
        
        print(f"✅ Query successful!")
        print(f"   Total records: {len(result.features)}")
        
        if result.features:
            print("\nExisting records:")
            for i, feature in enumerate(result.features[:5]):  # Show first 5
                print(f"   Record {i+1}: {feature.attributes}")
        else:
            print("   No existing records found (table is empty)")
        
        return result.features
        
    except Exception as e:
        print(f"❌ Query failed: {str(e)}")
        return None

def create_test_sensor_data():
    """Create test sensor data records"""
    test_records = [
        {
            "location": "Site1",
            "node_id": "NODE001",
            "block": "BLK001",  # Note: will be mapped to 'block_id' field
            "level": 2,
            "ward": "C2E",
            "asset_type": "plank",
            "asset_id": "C2E-208",
            "alarm_code": 3,
            "object_name": "early_deflection_alert",
            "description": "Early deflection alert",
            "present_value": 6.0,
            "threshold_value": 6.0,
            "min_value": -250.0,
            "max_value": 2.0,
            "resolution": 0.1,
            "units": "millimetre",
            "alarm_status": "InAlarm",
            "event_state": "HighLimit",
            "alarm_date": "2024-01-15T10:30:00.000Z",
            "device_type": "ultrasonic distance sensor"
        },
        {
            "location": "Site2",
            "node_id": "NODE002",
            "block": "BLK002",
            "level": 1,
            "ward": "C2E",
            "asset_type": "beam",
            "asset_id": "C2E-209",
            "alarm_code": 1,
            "object_name": "vibration_alert",
            "description": "Vibration threshold exceeded",
            "present_value": 2.5,
            "threshold_value": 2.0,
            "min_value": 0.0,
            "max_value": 10.0,
            "resolution": 0.01,
            "units": "hertz",
            "alarm_status": "Normal",
            "event_state": "Normal",
            "alarm_date": "2024-01-15T11:00:00.000Z",
            "device_type": "vibration sensor"
        }
    ]
    
    return test_records

def map_sensor_data_to_arcgis(sensor_data):
    """Map sensor data fields to ArcGIS field names"""
    # Field mappings based on the hosted table structure
    field_mappings = {
        'location': 'location',
        'node_id': 'node_id',
        'block': 'block_id',  # Note: sensor JSON has 'block' but table has 'block_id'
        'level': 'level',
        'ward': 'ward',
        'asset_type': 'asset_type',
        'asset_id': 'asset_id',
        'alarm_code': 'alarm_code',
        'object_name': 'object_name',
        'description': 'description',
        'present_value': 'present_value',
        'threshold_value': 'threshold_value',
        'min_value': 'min_value',
        'max_value': 'max_value',
        'resolution': 'resolution',
        'units': 'units',
        'alarm_status': 'alarm_status',
        'event_state': 'event_state',
        'alarm_date': 'alarm_date',
        'device_type': 'device_type'
    }
    
    # Map fields and convert date format
    mapped_data = {}
    for sensor_field, value in sensor_data.items():
        arcgis_field = field_mappings.get(sensor_field, sensor_field)
        
        # Handle date conversion
        if arcgis_field == 'alarm_date' and isinstance(value, str):
            try:
                # Parse ISO date string and convert to timestamp (milliseconds)
                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                # ArcGIS expects timestamp in milliseconds since epoch
                mapped_data[arcgis_field] = int(dt.timestamp() * 1000)
            except ValueError:
                print(f"Warning: Could not parse date {value}, using current time")
                mapped_data[arcgis_field] = int(datetime.now().timestamp() * 1000)
        else:
            mapped_data[arcgis_field] = value
    
    return mapped_data

def test_add_records(feature_layer):
    """Test adding records to the hosted table"""
    print("\n" + "=" * 60)
    print("Testing Add Records")
    print("=" * 60)
    
    try:
        # Create test sensor data
        test_records = create_test_sensor_data()
        
        print(f"Preparing to add {len(test_records)} test records...")
        
        # Prepare features for ArcGIS
        features_to_add = []
        for i, record in enumerate(test_records):
            print(f"\nPreparing record {i+1}:")
            print(f"   Asset ID: {record['asset_id']}")
            print(f"   Location: {record['location']}")
            print(f"   Device Type: {record['device_type']}")
            
            # Map sensor data to ArcGIS fields
            mapped_attributes = map_sensor_data_to_arcgis(record)
            
            feature = {
                "attributes": mapped_attributes
            }
            features_to_add.append(feature)
        
        # Add features to the table
        print(f"\nAdding {len(features_to_add)} features to the table...")
        result = feature_layer.edit_features(adds=features_to_add)
        
        print(f"✅ Add operation completed!")
        print(f"   Result: {result}")
        
        # Check if all records were added successfully
        if 'addResults' in result:
            success_count = sum(1 for r in result['addResults'] if r.get('success', False))
            print(f"   Successfully added: {success_count}/{len(features_to_add)} records")
            
            # Show any errors
            for i, add_result in enumerate(result['addResults']):
                if not add_result.get('success', False):
                    error_msg = add_result.get('error', {}).get('description', 'Unknown error')
                    print(f"   ❌ Record {i+1} failed: {error_msg}")
                else:
                    object_id = add_result.get('objectId', 'Unknown')
                    print(f"   ✅ Record {i+1} added with OBJECTID: {object_id}")
        
        return result
        
    except Exception as e:
        print(f"❌ Add records failed: {str(e)}")
        return None

def test_query_after_add(feature_layer):
    """Query records after adding to verify they were added"""
    print("\n" + "=" * 60)
    print("Verifying Records Were Added")
    print("=" * 60)
    
    try:
        # Query all records
        result = feature_layer.query(where="1=1", return_geometry=False)
        
        print(f"✅ Query after add successful!")
        print(f"   Total records now: {len(result.features)}")
        
        if result.features:
            print("\nRecords in table:")
            for i, feature in enumerate(result.features):
                attrs = feature.attributes
                print(f"   Record {i+1}:")
                print(f"      OBJECTID: {attrs.get('OBJECTID', 'N/A')}")
                print(f"      Asset ID: {attrs.get('asset_id', 'N/A')}")
                print(f"      Location: {attrs.get('location', 'N/A')}")
                print(f"      Device Type: {attrs.get('device_type', 'N/A')}")
                print(f"      Present Value: {attrs.get('present_value', 'N/A')}")
        
        return result.features
        
    except Exception as e:
        print(f"❌ Query after add failed: {str(e)}")
        return None

def main():
    """Main test function"""
    print("ArcGIS Online Connection Test")
    print("=" * 60)
    print("This script will test the connection to ArcGIS Online and add test records.")
    print("Make sure to update the credentials at the top of this file!")
    print("")
    
    # Check if credentials are still default
    if ARCGIS_USERNAME == "your-arcgis-username":
        print("❌ Please update the credentials at the top of this file!")
        print("   Set ARCGIS_USERNAME and ARCGIS_PASSWORD to your actual values.")
        return
    
    # Test connection
    gis = test_arcgis_connection()
    if not gis:
        print("❌ Cannot proceed without ArcGIS connection.")
        return
    
    # Test feature service access
    feature_layer = test_feature_service_access(gis)
    if not feature_layer:
        print("❌ Cannot proceed without feature service access.")
        return
    
    # Show table schema
    show_table_schema(feature_layer)
    
    # Query existing records
    existing_records = test_query_existing_records(feature_layer)
    
    # Ask user if they want to add test records
    print("\n" + "=" * 60)
    add_records = input("Do you want to add test records to the table? (y/n): ").lower().strip()
    
    if add_records == 'y':
        # Test adding records
        add_result = test_add_records(feature_layer)
        
        if add_result:
            # Verify records were added
            test_query_after_add(feature_layer)
    else:
        print("Skipping record addition.")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
    print("If all tests passed, your ArcGIS configuration is ready for the Azure Function.")

if __name__ == "__main__":
    main()