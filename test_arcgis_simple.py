#!/usr/bin/env python3
"""
Simplified test script for ArcGIS Online connection.
This version handles potential version compatibility issues.
"""

import sys
import os

# Configuration - Update with your credentials
ARCGIS_URL = "https://www.arcgis.com"
ARCGIS_USERNAME = "your-arcgis-username"  # Replace with your username
ARCGIS_PASSWORD = "your-arcgis-password"  # Replace with your password
FEATURE_SERVICE_ID = "your-feature-service-id"  # Replace with your service ID
FEATURE_LAYER_INDEX = 0

def test_imports():
    """Test if required modules can be imported"""
    print("=" * 60)
    print("Testing Module Imports")
    print("=" * 60)
    
    try:
        import arcgis
        print(f"✅ ArcGIS API imported successfully")
        print(f"   Version: {arcgis.__version__}")
    except ImportError as e:
        print(f"❌ Failed to import ArcGIS API: {e}")
        return False
    
    try:
        from arcgis.gis import GIS
        print("✅ GIS module imported")
    except ImportError as e:
        print(f"❌ Failed to import GIS module: {e}")
        return False
    
    try:
        from arcgis.features import FeatureLayer
        print("✅ FeatureLayer module imported")
    except ImportError as e:
        print(f"❌ Failed to import FeatureLayer module: {e}")
        return False
    
    return True

def test_connection():
    """Test basic connection to ArcGIS Online"""
    print("\n" + "=" * 60)
    print("Testing ArcGIS Online Connection")
    print("=" * 60)
    
    try:
        from arcgis.gis import GIS
        
        print(f"Connecting to: {ARCGIS_URL}")
        print(f"Username: {ARCGIS_USERNAME}")
        
        # Try to connect
        gis = GIS(ARCGIS_URL, ARCGIS_USERNAME, ARCGIS_PASSWORD)
        
        print("✅ Successfully connected!")
        print(f"   User: {gis.users.me.username}")
        print(f"   Organization: {gis.properties.name}")
        print(f"   Role: {gis.users.me.role}")
        
        return gis
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None

def test_service_access(gis):
    """Test access to the feature service"""
    print("\n" + "=" * 60)
    print("Testing Feature Service Access")
    print("=" * 60)
    
    try:
        print(f"Getting feature service: {FEATURE_SERVICE_ID}")
        feature_service = gis.content.get(FEATURE_SERVICE_ID)
        
        if not feature_service:
            print(f"❌ Feature service not found: {FEATURE_SERVICE_ID}")
            return None
        
        print("✅ Feature service found!")
        print(f"   Title: {feature_service.title}")
        print(f"   Type: {feature_service.type}")
        print(f"   Owner: {feature_service.owner}")
        print(f"   URL: {feature_service.url}")
        
        return feature_service
        
    except Exception as e:
        print(f"❌ Feature service access failed: {e}")
        return None

def test_layer_access(feature_service):
    """Test access to the feature layer/table"""
    print("\n" + "=" * 60)
    print("Testing Feature Layer/Table Access")
    print("=" * 60)
    
    try:
        print(f"Getting feature layer/table at index: {FEATURE_LAYER_INDEX}")
        
        # Check for both layers and tables
        layers = feature_service.layers if hasattr(feature_service, 'layers') else []
        tables = feature_service.tables if hasattr(feature_service, 'tables') else []
        
        print(f"Available layers: {len(layers)}")
        print(f"Available tables: {len(tables)}")
        
        # Try to get from tables first (since your service has tables)
        if tables and FEATURE_LAYER_INDEX < len(tables):
            feature_layer = tables[FEATURE_LAYER_INDEX]
            print("✅ Feature table found!")
            print(f"   Name: {feature_layer.properties.name}")
            print(f"   Type: {feature_layer.properties.type}")
            print(f"   URL: {feature_layer.url}")
            print(f"   Fields: {len(feature_layer.properties.fields)}")
            return feature_layer
        
        # Fall back to layers if no tables
        elif layers and FEATURE_LAYER_INDEX < len(layers):
            feature_layer = layers[FEATURE_LAYER_INDEX]
            print("✅ Feature layer found!")
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
        print(f"❌ Feature layer/table access failed: {e}")
        return None

def test_basic_query(feature_layer):
    """Test basic query operation"""
    print("\n" + "=" * 60)
    print("Testing Basic Query")
    print("=" * 60)
    
    try:
        # Simple query to get record count
        result = feature_layer.query(where="1=1", return_count_only=True)
        print(f"✅ Query successful!")
        print(f"   Total records: {result}")
        
        # Try to get actual records
        if result > 0:
            records = feature_layer.query(where="1=1", return_geometry=False, result_record_count=5)
            print(f"   Sample records: {len(records.features)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return False

def main():
    """Main test function"""
    print("ArcGIS Online Simple Connection Test")
    print("=" * 60)
    print(f"Python version: {sys.version}")
    print("")
    
    # Test imports
    if not test_imports():
        print("\n❌ Module import test failed. Cannot proceed.")
        print("Please check your ArcGIS API installation.")
        return False
    
    # Test connection
    gis = test_connection()
    if not gis:
        print("\n❌ Connection test failed. Cannot proceed.")
        print("Please check your credentials and network connection.")
        return False
    
    # Test service access
    feature_service = test_service_access(gis)
    if not feature_service:
        print("\n❌ Service access test failed. Cannot proceed.")
        print("Please check the feature service ID and permissions.")
        return False
    
    # Test layer access
    feature_layer = test_layer_access(feature_service)
    if not feature_layer:
        print("\n❌ Layer access test failed. Cannot proceed.")
        print("Please check the layer index and service configuration.")
        return False
    
    # Test basic query
    query_success = test_basic_query(feature_layer)
    if not query_success:
        print("\n❌ Query test failed.")
        print("The layer exists but queries are not working.")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 All Tests Passed!")
    print("=" * 60)
    print("Your ArcGIS Online connection is working correctly.")
    print("You can now proceed with Azure Functions deployment.")
    print("")
    print("Note: The Azure Functions deployment will use:")
    print("- Python 3.9")
    print("- ArcGIS API 1.9.1")
    print("- Same credentials and service ID")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)