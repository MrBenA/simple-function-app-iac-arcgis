# ArcGIS Connection Testing Setup

This guide will help you set up a virtual environment and test the ArcGIS Online connection before deploying to Azure Functions.

## Quick Setup (Recommended)

### Step 1: Run Setup Script
```bash
# Double-click or run from command prompt
setup_test_env.bat
```

This script will:
- Create a virtual environment
- Install all required dependencies (including ArcGIS API 1.9.1)
- Set up the testing environment

### Step 2: Configure Credentials
Edit `test_arcgis_connection.py` and update these lines:
```python
ARCGIS_USERNAME = "your-actual-username"  # Replace with your username
ARCGIS_PASSWORD = "your-actual-password"  # Replace with your password
```

### Step 3: Run Test
```bash
# Double-click or run from command prompt
run_test.bat
```

## Manual Setup (Alternative)

If you prefer to set up manually:

```bash
# Navigate to project directory
cd simple-function-app-iac-arcgis

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate.bat

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements-test.txt

# Update credentials in test_arcgis_connection.py
# Then run the test
python test_arcgis_connection.py
```

## What the Test Does

The test script (`test_arcgis_connection.py`) performs:

1. **Connection Test**: Verifies ArcGIS Online authentication
2. **Service Access**: Confirms access to the SensorDataService
3. **Schema Validation**: Shows table structure and field definitions
4. **Query Test**: Queries existing records (should be empty initially)
5. **Add Records Test**: Optionally adds test sensor data records
6. **Verification**: Confirms records were added successfully

## Expected Output

```
ArcGIS Online Connection Test
============================================================
✅ Successfully connected!
   User: your-username
   Organization: Your Organization
   Role: org_admin

✅ Feature service found!
   Title: SensorDataService
   Type: Feature Service
   Owner: your-username

✅ Feature layer found!
   Name: SensorReadings
   Type: Table
   URL: https://services-eu1.arcgis.com/.../SensorDataService/FeatureServer/0

Table Schema
============================================================
Total fields: 22

Field definitions:
   OBJECTID             | esriFieldTypeOID     | OBJECTID
   location             | esriFieldTypeString  | Location
   node_id              | esriFieldTypeString  | Node ID
   block_id             | esriFieldTypeString  | Block ID
   level                | esriFieldTypeInteger | Level
   ward                 | esriFieldTypeString  | Ward
   asset_type           | esriFieldTypeString  | Asset Type
   asset_id             | esriFieldTypeString  | Asset ID
   ...

✅ Query successful!
   Total records: 0 (initially empty)

Do you want to add test records to the table? (y/n): y

✅ Add operation completed!
   Successfully added: 2/2 records
```

## Troubleshooting

### Common Issues

1. **Virtual Environment Creation Fails**:
   - Ensure Python is installed and in PATH
   - Run command prompt as administrator if needed

2. **ArcGIS API Installation Takes Long**:
   - This is normal - the ArcGIS API is large
   - Installation may take 10-15 minutes

3. **Connection Fails**:
   - Verify your ArcGIS Online credentials
   - Check if your organization allows API access
   - Ensure you have permissions to access the SensorDataService

4. **Permission Errors**:
   - Make sure you have edit permissions on the SensorDataService
   - Check if the service is shared with your user

### Getting Help

If you encounter issues:
1. Check the error messages in the test output
2. Verify your ArcGIS Online account permissions
3. Ensure the SensorDataService exists and is accessible
4. Check the CLAUDE.md file for detailed troubleshooting

## Next Steps

Once the test passes:
1. You can proceed with Azure Functions deployment
2. The same credentials will be used in the Azure Function App settings
3. The service ID is already configured in the infrastructure templates

## Files Created

- `venv/` - Virtual environment directory
- `requirements-test.txt` - Testing dependencies
- `setup_test_env.bat` - Setup script
- `run_test.bat` - Test execution script
- `README_TESTING.md` - This file