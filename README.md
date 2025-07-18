# Simple Azure Function App with ArcGIS Integration - IaC

This is a specialized iteration of the simple Azure Function App project, building on the proven [simple-function-app-iac](../simple-function-app-iac) implementation. This iteration focuses on receiving sensor data via REST API and writing it to ArcGIS Online hosted feature services.

## Features

- **Sensor Data Ingestion**: Receive JSON sensor data via REST API POST requests
- **ArcGIS Online Integration**: Write sensor data to hosted feature services
- **Data Validation**: Pydantic models for robust sensor data validation
- **Automatic Add/Update**: Intelligent feature add or update based on asset_id
- **Field Mapping**: Configurable mapping between sensor fields and ArcGIS fields
- **Health Monitoring**: Enhanced health check with ArcGIS connection validation
- **Infrastructure as Code**: Bicep templates for complete automation

## Architecture

### Infrastructure Components

- **Function App**: Linux-based with Python 3.9 runtime (compatible with ArcGIS API)
- **Storage Account**: Function app storage
- **Application Insights**: Monitoring and logging
- **Hosting Plan**: Consumption (serverless) plan

### ArcGIS Integration

- **ArcGIS Online**: Connection to ArcGIS organization
- **Hosted Feature Service**: Standard (non-geometry) table for sensor data
- **Authentication**: Username/password stored in Azure Function App settings
- **API Version**: ArcGIS Python API 1.9.1 (compatible with Azure Functions)

## Project Structure

```
simple-function-app-iac-arcgis/
├── src/                          # Function code
│   ├── function_app.py           # Main function app with ArcGIS integration
│   ├── config.py                 # Configuration management for ArcGIS
│   ├── host.json                 # Function host configuration (10min timeout)
│   └── requirements.txt          # Python dependencies (arcgis==1.9.1)
├── infra/                        # Infrastructure as Code
│   ├── main.bicep                # Bicep template with ArcGIS settings
│   └── main.bicepparam           # ArcGIS-specific parameters
├── .github/workflows/            # GitHub Actions
│   ├── deploy-infra.yml          # Infrastructure deployment
│   └── deploy-app.yml            # Application deployment
├── README.md                     # This file
└── CLAUDE.md                     # Comprehensive development guidance
```

## Sensor Data Format

The function app expects sensor data in the following JSON format:

```json
{
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
```

## API Endpoints

### Sensor Data Ingestion

```bash
# POST sensor data
curl -X POST "https://your-function-app.azurewebsites.net/api/sensor-data" \
  -H "Content-Type: application/json" \
  -d '{
    "location": "test-location",
    "node_id": "test-node",
    "asset_id": "blk-001-208",
    "alarm_code": 3,
    "present_value": 6.0,
    "alarm_date": "2024-01-15T10:30:00.000Z",
    "device_type": "ultrasonic distance sensor"
  }'
```

### Feature Queries

```bash
# Get feature by asset ID
curl "https://your-function-app.azurewebsites.net/api/features/blk-001-208"

# List all features (with optional filtering)
curl "https://your-function-app.azurewebsites.net/api/features?limit=10&where=alarm_code=3"

# Health check with ArcGIS validation
curl "https://your-function-app.azurewebsites.net/api/health"
```

## Configuration

### ArcGIS Online Setup

1. **Create Hosted Feature Service**:
   - Create a new hosted feature service in ArcGIS Online
   - Configure table schema to match sensor data fields
   - Note the feature service ID

2. **Field Schema Requirements**:
   ```
   location (Text)
   node_id (Text)
   block (Text)
   level (Integer)
   ward (Text)
   asset_type (Text)
   asset_id (Text) - Primary key for updates
   alarm_code (Integer)
   object_name (Text)
   description (Text)
   present_value (Double)
   threshold_value (Double)
   min_value (Double)
   max_value (Double)
   resolution (Double)
   units (Text)
   alarm_status (Text)
   event_state (Text)
   alarm_date (Date)
   device_type (Text)
   record_created (Date) - Auto-generated
   ```

### Azure Function App Settings

The following environment variables are required:

```bash
ARCGIS_URL=https://www.arcgis.com
ARCGIS_USERNAME=your-arcgis-username
ARCGIS_PASSWORD=your-arcgis-password
FEATURE_SERVICE_ID=your-feature-service-id
FEATURE_LAYER_INDEX=0
```

## Deployment

### Prerequisites

1. **Azure Subscription** with appropriate permissions
2. **ArcGIS Online Account** with feature service creation rights
3. **GitHub Repository** with secrets configured
4. **Azure CLI** (for local development)

### Setup GitHub Secrets

Add the following secrets to your GitHub repository:

```
AZURE_CREDENTIALS = {
  "clientId": "your-service-principal-client-id",
  "clientSecret": "your-service-principal-client-secret",
  "subscriptionId": "your-azure-subscription-id",
  "tenantId": "your-azure-tenant-id"
}

# Optional: Store ArcGIS credentials as secrets
ARCGIS_USERNAME = "your-arcgis-username"
ARCGIS_PASSWORD = "your-arcgis-password"
FEATURE_SERVICE_ID = "your-feature-service-id"
FEATURE_LAYER_INDEX = "0"
```

### Deployment Steps

1. **Deploy Infrastructure**:
   - Push changes to `infra/` folder OR
   - Manually trigger "Deploy ArcGIS Infrastructure" workflow
   - Provide ArcGIS credentials when prompted

2. **Deploy Application**:
   - Push changes to `src/` folder OR
   - Manually trigger "Deploy ArcGIS Function App" workflow
   - Function app will be deployed with ArcGIS integration

## Development

### Local Development

```bash
# Navigate to src directory
cd src

# Install dependencies (may take time for ArcGIS API)
pip install -r requirements.txt

# Set environment variables
export ARCGIS_URL="https://www.arcgis.com"
export ARCGIS_USERNAME="your-username"
export ARCGIS_PASSWORD="your-password"
export FEATURE_SERVICE_ID="your-service-id"
export FEATURE_LAYER_INDEX="0"

# Run locally (requires Azure Functions Core Tools)
func start
```

### Testing Locally

```bash
# Test health endpoint
curl http://localhost:7071/api/health

# Test sensor data ingestion
curl -X POST http://localhost:7071/api/sensor-data \
  -H "Content-Type: application/json" \
  -d '{
    "location": "test-location",
    "node_id": "test-node",
    "asset_id": "test-001",
    "alarm_code": 1,
    "present_value": 5.5,
    "alarm_date": "2024-01-15T10:30:00.000Z",
    "device_type": "test sensor"
  }'

# Test feature query
curl http://localhost:7071/api/features/test-001
```

## Data Flow

1. **Sensor Data Received**: Function receives JSON sensor data via POST request
2. **Data Validation**: Pydantic model validates all required fields
3. **ArcGIS Connection**: Function connects to ArcGIS Online using stored credentials
4. **Feature Service Query**: Check if feature exists based on `asset_id`
5. **Add or Update**: Either add new feature or update existing feature
6. **Response**: Return success/failure with operation details

## Known Limitations

### ArcGIS Python API Compatibility

- **Version Constraint**: Must use `arcgis==1.9.1` for reliable Azure Functions deployment
- **Deployment Time**: ArcGIS API installation increases deployment time significantly
- **Python Version**: Requires Python 3.9 for optimal compatibility
- **Memory Usage**: ArcGIS API has higher memory requirements

### Azure Functions Constraints

- **Timeout**: Extended to 10 minutes due to ArcGIS API initialization
- **Cold Start**: Initial connections may take longer due to ArcGIS API loading
- **Linux Only**: Python runtime requires Linux hosting plan

## Troubleshooting

### Common Issues

1. **ArcGIS Connection Failures**:
   - Verify credentials in Azure Function App settings
   - Check feature service ID and permissions
   - Ensure ArcGIS Online organization is accessible

2. **Deployment Failures**:
   - Confirm using `arcgis==1.9.1` in requirements.txt
   - Verify Python 3.9 runtime
   - Check Azure Functions deployment logs

3. **Data Validation Errors**:
   - Ensure JSON matches expected sensor data format
   - Check date format in `alarm_date` field
   - Verify all required fields are present

### Health Check

The `/api/health` endpoint provides comprehensive status:

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0-arcgis",
  "dependencies": {
    "arcgis_online": "healthy",
    "feature_service": "healthy"
  },
  "arcgis_user": "your-username",
  "arcgis_org": "Your Organization",
  "feature_layer": "Sensor Data Layer"
}
```

## Support

This project demonstrates ArcGIS integration with Azure Functions:

1. Understand [simple-function-app-iac](../simple-function-app-iac) for IaC basics
2. Review [CLAUDE.md](CLAUDE.md) for comprehensive development guidance
3. Check ArcGIS Python API documentation for advanced features

For production use, consider:
- Managed Identity for Azure authentication
- ArcGIS token-based authentication
- Error handling and retry logic
- Monitoring and alerting
- Data backup and recovery