# Sensor Data Ingestion Feature

## Overview

The sensor data ingestion feature provides a REST API endpoint for receiving JSON sensor data and storing it as historical records in ArcGIS Online hosted feature services. This feature implements a historical data model where each POST request creates a new record, maintaining a complete audit trail of sensor readings over time.

## API Endpoint

### POST /api/sensor-data

**Purpose**: Accept JSON sensor data and create historical records in ArcGIS Online

**HTTP Method**: POST  
**Content-Type**: application/json  
**Authentication**: Anonymous (development) / API Key (production)

## Request Format

### Complete Sensor Data JSON Schema

All 20 fields are required for successful processing:

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

### Field Requirements

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| location | String | ✅ | Sensor installation location | "building-a-floor-2" |
| node_id | String | ✅ | Network node identifier | "node-001" |
| block | String | ✅ | Building block identifier | "blk-001" |
| level | Integer | ✅ | Floor/level number | 2 |
| ward | String | ✅ | Ward or zone identifier | "ward-a" |
| asset_type | String | ✅ | Type of monitored asset | "plank", "beam", "column" |
| asset_id | String | ✅ | Unique asset identifier | "blk-001-208" |
| alarm_code | Integer | ✅ | Numeric alarm classification | 1, 2, 3, 4, 5 |
| object_name | String | ✅ | Alarm object name | "deflection_alert" |
| description | String | ✅ | Human-readable description | "Early deflection detected" |
| present_value | Float | ✅ | Current sensor reading | 6.0 |
| threshold_value | Float | ✅ | Alarm threshold setting | 5.0 |
| min_value | Float | ✅ | Sensor minimum range | -250.0 |
| max_value | Float | ✅ | Sensor maximum range | 250.0 |
| resolution | Float | ✅ | Sensor measurement resolution | 0.1 |
| units | String | ✅ | Measurement units | "millimetre", "celsius" |
| alarm_status | String | ✅ | Current alarm state | "InAlarm", "Normal" |
| event_state | String | ✅ | Event classification | "HighLimit", "LowLimit" |
| alarm_date | String | ✅ | ISO 8601 timestamp | "2024-01-15T10:30:00.000Z" |
| device_type | String | ✅ | Sensor device type | "ultrasonic distance sensor" |

## Data Validation

### Validation Rules

1. **Required Fields**: All 20 fields must be present in the JSON payload
2. **Data Types**: String, Integer, Float types validated according to schema
3. **Date Format**: alarm_date must be valid ISO 8601 format
4. **Field Lengths**: String fields respect ArcGIS table column limits
5. **Numeric Ranges**: Numeric values validated for reasonable ranges

### Validation Implementation

```python
@dataclass
class SensorData:
    location: str
    node_id: str
    block: str
    level: int
    ward: str
    asset_type: str
    asset_id: str
    alarm_code: int
    object_name: str
    description: str
    present_value: float
    threshold_value: float
    min_value: float
    max_value: float
    resolution: float
    units: str
    alarm_status: str
    event_state: str
    alarm_date: str
    device_type: str
```

### Error Response Format

**400 Bad Request** - Validation failures:
```json
{
  "error": "Missing required field: asset_id",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "status_code": 400
}
```

**400 Bad Request** - Invalid data types:
```json
{
  "error": "Invalid data type for field 'level': expected int, got str",
  "timestamp": "2024-01-15T10:30:00.000Z", 
  "status_code": 400
}
```

## Response Format

### Success Response (200 OK)

```json
{
  "status": "success",
  "message": "Historical sensor data record created successfully",
  "asset_id": "blk-001-208",
  "operation": "add",
  "alarm_date": "2024-01-15T10:30:00.000Z",
  "processed_timestamp": "2024-01-15T10:30:05.123Z",
  "arcgis_objectid": 12345
}
```

### Error Responses

**500 Internal Server Error** - ArcGIS operation failure:
```json
{
  "error": "Failed to create feature record",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "status_code": 500
}
```

## Data Processing Workflow

### 1. Request Reception
- HTTP POST request received by Azure Function
- Content-Type validation (application/json required)
- JSON payload parsing and initial validation

### 2. Data Validation
- SensorData dataclass instantiation with type checking
- Required field validation (all 20 fields)
- Data type conversion and validation
- Date format validation and parsing

### 3. Field Mapping
- JSON field names mapped to ArcGIS table column names
- Special handling for 'block' → 'block_id' mapping
- Date string conversion to ArcGIS timestamp format (milliseconds)
- Addition of processing timestamp for audit trail

### 4. ArcGIS Integration
- Authentication token retrieval and validation
- Feature service connection establishment
- Add features operation via REST API
- Response validation and error handling

### 5. Response Generation
- Success response with operation details
- Error response with specific failure information
- Logging of all operations for monitoring

## Historical Data Model

### Core Principles

1. **Append-Only**: Each POST creates a new record, never updates existing records
2. **Complete Audit Trail**: All sensor readings preserved with timestamps
3. **Asset Timeline**: Multiple records per asset_id showing readings over time
4. **Processing Metadata**: Each record includes original and processing timestamps

### Benefits

- **Data Integrity**: Original sensor readings never modified or lost
- **Trend Analysis**: Complete historical data available for analysis
- **Compliance**: Full audit trail for regulatory requirements
- **Debugging**: Ability to track data processing and transformation

### Storage Pattern

```
asset_id: "blk-001-208"
├── Record 1: 2024-01-15T08:00:00Z (present_value: 4.5, alarm_status: "Normal")
├── Record 2: 2024-01-15T09:00:00Z (present_value: 5.2, alarm_status: "Normal")  
├── Record 3: 2024-01-15T10:30:00Z (present_value: 6.0, alarm_status: "InAlarm")
└── Record 4: 2024-01-15T11:15:00Z (present_value: 6.2, alarm_status: "InAlarm")
```

## Performance Considerations

### Throughput Characteristics
- **Single Record Processing**: Optimized for individual sensor readings
- **Processing Time**: ~500ms average per record including ArcGIS write
- **Concurrent Requests**: Azure Functions auto-scaling handles multiple requests
- **Rate Limits**: ArcGIS Online allows 1000 requests/minute per token

### Optimization Strategies
- **Connection Reuse**: ArcGIS authentication token cached and reused
- **Minimal Dependencies**: urllib-based implementation for fast cold starts
- **Error Handling**: Fast-fail validation to minimize processing overhead
- **Logging**: Structured logging for performance monitoring

## Testing Examples

### Minimal Test Data
```bash
curl -X POST http://localhost:7071/api/sensor-data \
  -H "Content-Type: application/json" \
  -d '{
    "location": "test-location",
    "node_id": "test-node",
    "block": "test-block",
    "level": 1,
    "ward": "test-ward", 
    "asset_type": "test-asset",
    "asset_id": "test-001",
    "alarm_code": 1,
    "object_name": "test_alert",
    "description": "Test sensor reading",
    "present_value": 5.5,
    "threshold_value": 5.0,
    "min_value": 0.0,
    "max_value": 10.0,
    "resolution": 0.1,
    "units": "units",
    "alarm_status": "Normal",
    "event_state": "Normal",
    "alarm_date": "2024-01-15T10:30:00.000Z",
    "device_type": "test sensor"
  }'
```

### Production Test Data
```bash
curl -X POST https://your-function-app.azurewebsites.net/api/sensor-data \
  -H "Content-Type: application/json" \
  -d @production-sensor-data.json
```

## Known Issues & Limitations

### Current Limitations
- **Batch Processing**: No support for multiple sensor readings in single request
- **Rate Limiting**: No built-in rate limiting (relies on ArcGIS limits)
- **Retry Logic**: No automatic retry for failed ArcGIS operations
- **Authentication**: Anonymous access in development mode

### Compatibility Issues
- **Date Format Sensitivity**: Strict ISO 8601 format required
- **Field Name Mapping**: 'block' JSON field maps to 'block_id' in ArcGIS
- **Numeric Precision**: Float values limited by ArcGIS Double precision
- **String Length Limits**: ArcGIS field length constraints apply

### Future Enhancements
- **Batch Processing**: Support for multiple sensor readings per request
- **Authentication**: API key or token-based authentication
- **Rate Limiting**: Per-client request rate limiting
- **Retry Logic**: Automatic retry with exponential backoff
- **Validation Rules**: Configurable validation rules per sensor type

## Error Handling Patterns

### Validation Errors
```python
try:
    sensor_data = validate_sensor_data(req_body)
except ValidationError as e:
    return func.HttpResponse(
        json.dumps({"error": f"Invalid sensor data: {str(e)}"}),
        status_code=400,
        mimetype="application/json"
    )
```

### ArcGIS Integration Errors
```python
try:
    result = feature_service.add_features([sensor_data])
except Exception as e:
    logging.error(f"ArcGIS operation failed: {str(e)}")
    return func.HttpResponse(
        json.dumps({"error": "Failed to store sensor data"}),
        status_code=500,
        mimetype="application/json"
    )
```

---

**Implementation Status**: ✅ Complete - Phase 3 implementation with comprehensive validation, error handling, and historical data storage patterns.