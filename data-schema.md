# Data Schema Reference

## Overview

This document provides the complete data schema reference for sensor data processing, including the 20-field sensor data structure, ArcGIS table schema, field mappings, validation rules, and data transformation patterns used throughout the system.

## Sensor Data Schema

### Complete Field Structure

The sensor data JSON schema consists of 20 required fields representing a comprehensive sensor reading with metadata, measurement values, and alarm information:

```json
{
  "location": "building-a-floor-2",
  "node_id": "node-001",
  "block": "blk-001", 
  "level": 2,
  "ward": "ward-a",
  "asset_type": "plank",
  "asset_id": "blk-001-208",
  "alarm_code": 3,
  "object_name": "early_deflection_alert",
  "description": "Early deflection alert detected",
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
}
```

## Field Specifications

### Location & Identification Fields

| Field | Type | Required | Max Length | Description | Example Values |
|-------|------|----------|------------|-------------|----------------|
| **location** | String | ✅ | 100 | Physical installation location | "building-a-floor-2", "roof-section-c" |
| **node_id** | String | ✅ | 50 | Network node identifier | "node-001", "gateway-b-12" |
| **block** | String | ✅ | 50 | Building block or section | "blk-001", "section-a", "zone-3" |
| **level** | Integer | ✅ | - | Floor or vertical level | 0, 1, 2, -1 (basement) |
| **ward** | String | ✅ | 10 | Administrative ward/zone | "ward-a", "zone-1", "sector-b" |
| **asset_type** | String | ✅ | 50 | Type of monitored structure | "plank", "beam", "column", "slab" |
| **asset_id** | String | ✅ | 50 | Unique asset identifier | "blk-001-208", "beam-a-15" |

### Measurement Fields

| Field | Type | Required | Description | Example Values | Units |
|-------|------|----------|-------------|----------------|-------|
| **present_value** | Float | ✅ | Current sensor measurement | 6.0, -2.5, 150.75 | Various |
| **threshold_value** | Float | ✅ | Configured alarm threshold | 5.0, 100.0, -10.0 | Same as present_value |
| **min_value** | Float | ✅ | Sensor minimum range | -250.0, 0.0, -100.0 | Same as present_value |
| **max_value** | Float | ✅ | Sensor maximum range | 250.0, 1000.0, 50.0 | Same as present_value |
| **resolution** | Float | ✅ | Measurement precision | 0.1, 0.01, 1.0 | Same as present_value |
| **units** | String | ✅ | Measurement units | "millimetre", "celsius", "pascal" | - |

### Alarm & Status Fields

| Field | Type | Required | Max Length | Description | Valid Values |
|-------|------|----------|------------|-------------|--------------|
| **alarm_code** | Integer | ✅ | - | Numeric alarm classification | 1, 2, 3, 4, 5 |
| **object_name** | String | ✅ | 100 | System object/alert name | "deflection_alert", "temp_warning" |
| **description** | String | ✅ | 255 | Human-readable description | "Early deflection detected" |
| **alarm_status** | String | ✅ | 20 | Current alarm state | "Normal", "InAlarm", "Warning" |
| **event_state** | String | ✅ | 20 | Event type classification | "Normal", "HighLimit", "LowLimit" |
| **alarm_date** | String | ✅ | - | ISO 8601 timestamp | "2024-01-15T10:30:00.000Z" |
| **device_type** | String | ✅ | 100 | Sensor hardware description | "ultrasonic distance sensor" |

## ArcGIS Table Schema

### Hosted Feature Service Structure

**Service Details:**
- **Service Name**: SensorDataService
- **Table Name**: SensorReadings
- **Service ID**: f4682a40e60847fe8289408e73933b82
- **Total Fields**: 22 (20 sensor fields + OBJECTID + processing timestamp)

### ArcGIS Field Definitions

| Field Name | ArcGIS Type | Alias | Length | Allow Nulls | Description |
|------------|-------------|-------|--------|-------------|-------------|
| **OBJECTID** | esriFieldTypeOID | OBJECTID | - | No | Auto-generated unique identifier |
| **location** | esriFieldTypeString | Location | 100 | No | Sensor installation location |
| **node_id** | esriFieldTypeString | Node ID | 50 | No | Network node identifier |
| **block_id** | esriFieldTypeString | Block ID | 50 | No | Building block identifier |
| **level** | esriFieldTypeInteger | Level | - | No | Floor/level number |
| **ward** | esriFieldTypeString | Ward | 10 | No | Ward or zone identifier |
| **asset_type** | esriFieldTypeString | Asset Type | 50 | No | Type of monitored asset |
| **asset_id** | esriFieldTypeString | Asset ID | 50 | No | Unique asset identifier |
| **alarm_code** | esriFieldTypeInteger | Alarm Code | - | No | Numeric alarm classification |
| **object_name** | esriFieldTypeString | Object Name | 100 | No | System object/alert name |
| **description** | esriFieldTypeString | Description | 255 | No | Human-readable description |
| **present_value** | esriFieldTypeDouble | Present Value | - | No | Current sensor measurement |
| **threshold_value** | esriFieldTypeDouble | Threshold Value | - | No | Configured alarm threshold |
| **min_value** | esriFieldTypeDouble | Min Value | - | No | Sensor minimum range |
| **max_value** | esriFieldTypeDouble | Max Value | - | No | Sensor maximum range |
| **resolution** | esriFieldTypeDouble | Resolution | - | No | Measurement precision |
| **units** | esriFieldTypeString | Units | 20 | No | Measurement units |
| **alarm_status** | esriFieldTypeString | Alarm Status | 20 | No | Current alarm state |
| **event_state** | esriFieldTypeString | Event State | 20 | No | Event type classification |
| **alarm_date** | esriFieldTypeDate | Alarm Date | - | No | Original timestamp (milliseconds) |
| **device_type** | esriFieldTypeString | Device Type | 100 | No | Sensor hardware description |
| **record_created** | esriFieldTypeDate | Record Created | - | No | Processing timestamp (milliseconds) |

## Field Mapping Configuration

### JSON to ArcGIS Mapping

The following mapping converts sensor JSON fields to ArcGIS table columns:

```python
FIELD_MAPPINGS = {
    # Location & Identification
    'location': 'location',
    'node_id': 'node_id', 
    'block': 'block_id',           # Special mapping: JSON 'block' → ArcGIS 'block_id'
    'level': 'level',
    'ward': 'ward',
    'asset_type': 'asset_type',
    'asset_id': 'asset_id',
    
    # Alarm Information
    'alarm_code': 'alarm_code',
    'object_name': 'object_name',
    'description': 'description',
    'alarm_status': 'alarm_status',
    'event_state': 'event_state',
    'alarm_date': 'alarm_date',
    
    # Measurement Values
    'present_value': 'present_value',
    'threshold_value': 'threshold_value',
    'min_value': 'min_value',
    'max_value': 'max_value',
    'resolution': 'resolution',
    'units': 'units',
    
    # Device Information
    'device_type': 'device_type'
}
```

### Special Field Handling

#### Block Field Mapping
```python
# JSON input has 'block' field
{"block": "blk-001"}

# Maps to ArcGIS 'block_id' field
{"block_id": "blk-001"}
```

#### Date Conversion
```python
# JSON input: ISO 8601 string
{"alarm_date": "2024-01-15T10:30:00.000Z"}

# Converted to ArcGIS timestamp (milliseconds since epoch)
{"alarm_date": 1705312200000}

# Conversion logic:
def convert_iso_to_arcgis_timestamp(iso_string):
    dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
    return int(dt.timestamp() * 1000)
```

#### Processing Timestamp Addition
```python
# Automatically added during processing
processing_time = datetime.now()
attributes['record_created'] = int(processing_time.timestamp() * 1000)
```

## Data Validation Rules

### Required Field Validation

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class SensorData:
    """Sensor data validation using Python dataclass"""
    location: str
    node_id: str
    block: str              # Note: maps to 'block_id' in ArcGIS
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
    alarm_date: str         # ISO 8601 string format
    device_type: str
    
    def __post_init__(self):
        """Additional validation after initialization"""
        self.validate_numeric_ranges()
        self.validate_date_format()
        self.validate_string_lengths()
    
    def validate_numeric_ranges(self):
        """Validate numeric field relationships"""
        if self.min_value >= self.max_value:
            raise ValueError("min_value must be less than max_value")
        
        if not (self.min_value <= self.present_value <= self.max_value):
            raise ValueError("present_value must be within min_value and max_value range")
        
        if self.resolution <= 0:
            raise ValueError("resolution must be positive")
    
    def validate_date_format(self):
        """Validate ISO 8601 date format"""
        try:
            datetime.fromisoformat(self.alarm_date.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError(f"Invalid date format: {self.alarm_date}. Expected ISO 8601.")
    
    def validate_string_lengths(self):
        """Validate string field lengths against ArcGIS limits"""
        length_limits = {
            'location': 100, 'node_id': 50, 'block': 50, 'ward': 10,
            'asset_type': 50, 'asset_id': 50, 'object_name': 100,
            'description': 255, 'units': 20, 'alarm_status': 20,
            'event_state': 20, 'device_type': 100
        }
        
        for field, limit in length_limits.items():
            value = getattr(self, field)
            if len(value) > limit:
                raise ValueError(f"{field} exceeds maximum length of {limit} characters")
```

### Data Type Validation

```python
def validate_sensor_data(json_data):
    """Validate JSON sensor data against schema"""
    required_fields = [
        'location', 'node_id', 'block', 'level', 'ward', 'asset_type', 
        'asset_id', 'alarm_code', 'object_name', 'description',
        'present_value', 'threshold_value', 'min_value', 'max_value',
        'resolution', 'units', 'alarm_status', 'event_state',
        'alarm_date', 'device_type'
    ]
    
    # Check required fields
    missing_fields = [field for field in required_fields if field not in json_data]
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
    
    # Type validation
    type_validators = {
        'level': lambda x: isinstance(x, int),
        'alarm_code': lambda x: isinstance(x, int),
        'present_value': lambda x: isinstance(x, (int, float)),
        'threshold_value': lambda x: isinstance(x, (int, float)),
        'min_value': lambda x: isinstance(x, (int, float)),
        'max_value': lambda x: isinstance(x, (int, float)),
        'resolution': lambda x: isinstance(x, (int, float))
    }
    
    for field, validator in type_validators.items():
        if not validator(json_data[field]):
            raise ValueError(f"Invalid type for field '{field}': expected numeric")
    
    # Create validated sensor data object
    return SensorData(**json_data)
```

## Data Transformation Patterns

### Complete Transformation Pipeline

```python
def transform_sensor_data_to_arcgis(sensor_data):
    """Complete transformation from sensor JSON to ArcGIS attributes"""
    attributes = {}
    
    # Apply field mappings
    for json_field, arcgis_field in FIELD_MAPPINGS.items():
        if hasattr(sensor_data, json_field):
            value = getattr(sensor_data, json_field)
            
            # Apply special transformations
            if json_field == 'alarm_date':
                # Convert ISO string to milliseconds
                value = convert_iso_to_arcgis_timestamp(value)
            elif json_field in ['present_value', 'threshold_value', 'min_value', 'max_value', 'resolution']:
                # Ensure numeric values are properly typed
                value = float(value)
            elif json_field in ['level', 'alarm_code']:
                # Ensure integer values are properly typed
                value = int(value)
            else:
                # String fields - ensure proper encoding
                value = str(value)
            
            attributes[arcgis_field] = value
    
    # Add processing metadata
    processing_time = datetime.now()
    attributes['record_created'] = int(processing_time.timestamp() * 1000)
    
    return attributes
```

### Reverse Transformation (ArcGIS to JSON)

```python
def transform_arcgis_to_sensor_json(arcgis_attributes):
    """Transform ArcGIS attributes back to sensor JSON format"""
    reverse_mappings = {v: k for k, v in FIELD_MAPPINGS.items()}
    
    sensor_json = {}
    
    for arcgis_field, value in arcgis_attributes.items():
        if arcgis_field in reverse_mappings:
            json_field = reverse_mappings[arcgis_field]
            
            # Apply reverse transformations
            if arcgis_field == 'alarm_date':
                # Convert milliseconds back to ISO string
                if value:
                    dt = datetime.fromtimestamp(value / 1000, tz=timezone.utc)
                    value = dt.isoformat().replace('+00:00', 'Z')
            
            sensor_json[json_field] = value
    
    return sensor_json
```

## Usage Examples

### Sample Sensor Data Types

#### Structural Monitoring Sensor
```json
{
  "location": "building-a-floor-3",
  "node_id": "structural-node-05",
  "block": "blk-003",
  "level": 3,
  "ward": "structural-zone-a",
  "asset_type": "beam",
  "asset_id": "beam-a-305",
  "alarm_code": 2,
  "object_name": "deflection_monitoring",
  "description": "Structural beam deflection measurement",
  "present_value": 3.2,
  "threshold_value": 5.0,
  "min_value": -10.0,
  "max_value": 15.0,
  "resolution": 0.1,
  "units": "millimetre",
  "alarm_status": "Normal",
  "event_state": "Normal",
  "alarm_date": "2024-01-15T14:22:00.000Z",
  "device_type": "laser displacement sensor"
}
```

#### Temperature Monitoring Sensor
```json
{
  "location": "server-room-basement",
  "node_id": "env-node-12",
  "block": "basement",
  "level": -1,
  "ward": "facilities",
  "asset_type": "environment",
  "asset_id": "temp-sensor-b01",
  "alarm_code": 4,
  "object_name": "temperature_alert",
  "description": "Server room temperature exceeds threshold",
  "present_value": 28.5,
  "threshold_value": 25.0,
  "min_value": 10.0,
  "max_value": 40.0,
  "resolution": 0.1,
  "units": "celsius",
  "alarm_status": "InAlarm",
  "event_state": "HighLimit", 
  "alarm_date": "2024-01-15T15:45:30.000Z",
  "device_type": "digital temperature sensor"
}
```

#### Vibration Monitoring Sensor
```json
{
  "location": "machinery-room-floor-1",
  "node_id": "vibration-node-03",
  "block": "industrial-section",
  "level": 1,
  "ward": "maintenance",
  "asset_type": "machinery",
  "asset_id": "pump-station-01",
  "alarm_code": 1,
  "object_name": "vibration_normal",
  "description": "Pump vibration within normal parameters",
  "present_value": 2.1,
  "threshold_value": 5.0,
  "min_value": 0.0,
  "max_value": 20.0,
  "resolution": 0.01,
  "units": "mm/s",
  "alarm_status": "Normal",
  "event_state": "Normal",
  "alarm_date": "2024-01-15T16:10:15.000Z",
  "device_type": "piezoelectric accelerometer"
}
```

## Schema Evolution & Versioning

### Schema Version Management

```python
class SensorDataSchemaV1:
    """Version 1.0 of sensor data schema"""
    VERSION = "1.0"
    REQUIRED_FIELDS = 20
    SUPPORTS_BATCH = False

# Future version example
class SensorDataSchemaV2:
    """Future version 2.0 with additional fields"""
    VERSION = "2.0" 
    REQUIRED_FIELDS = 25  # Additional fields added
    SUPPORTS_BATCH = True
    NEW_FIELDS = ['sensor_serial_number', 'calibration_date', 'maintenance_due', 'location_coordinates', 'installation_date']
```

### Backward Compatibility

```python
def handle_schema_migration(sensor_data, from_version, to_version):
    """Handle schema migration between versions"""
    if from_version == "1.0" and to_version == "2.0":
        # Add default values for new fields
        sensor_data.update({
            'sensor_serial_number': 'unknown',
            'calibration_date': None,
            'maintenance_due': None,
            'location_coordinates': None,
            'installation_date': None
        })
    
    return sensor_data
```

## Data Quality & Integrity

### Quality Validation Rules

```python
class DataQualityValidator:
    """Advanced data quality validation"""
    
    @staticmethod
    def validate_measurement_consistency(sensor_data):
        """Validate measurement value consistency"""
        issues = []
        
        # Check if present_value is reasonable given min/max
        range_size = sensor_data.max_value - sensor_data.min_value
        if abs(sensor_data.present_value - sensor_data.threshold_value) > range_size:
            issues.append("Present value significantly different from threshold")
        
        # Check resolution appropriateness
        if sensor_data.resolution >= range_size / 10:
            issues.append("Resolution too coarse for measurement range")
        
        return issues
    
    @staticmethod
    def validate_temporal_consistency(current_reading, previous_readings):
        """Validate temporal consistency across readings"""
        if not previous_readings:
            return []
        
        issues = []
        latest_previous = max(previous_readings, key=lambda x: x.alarm_date)
        
        # Check for reasonable value change
        value_change = abs(current_reading.present_value - latest_previous.present_value)
        max_expected_change = abs(current_reading.max_value - current_reading.min_value) * 0.1
        
        if value_change > max_expected_change:
            issues.append("Unusually large value change from previous reading")
        
        return issues
```

### Data Normalization Patterns

```python
def normalize_sensor_data(raw_data):
    """Normalize sensor data for consistency"""
    normalized = {}
    
    for field, value in raw_data.items():
        if field == 'location':
            # Normalize location strings
            normalized[field] = value.lower().strip().replace(' ', '-')
        elif field == 'units':
            # Standardize unit names
            unit_mappings = {
                'mm': 'millimetre',
                'deg_c': 'celsius',
                'pa': 'pascal',
                'hz': 'hertz'
            }
            normalized[field] = unit_mappings.get(value.lower(), value)
        elif field in ['alarm_status', 'event_state']:
            # Standardize status values
            normalized[field] = value.title()  # "inAlarm" -> "InAlarm"
        else:
            normalized[field] = value
    
    return normalized
```

## Performance Considerations

### Indexing Strategy

For optimal query performance in ArcGIS, consider these indexing recommendations:

```python
RECOMMENDED_INDEXES = {
    'primary_queries': [
        'asset_id',           # Most common query field
        'alarm_date',         # Time-based queries
        'location',           # Location-based queries
        'alarm_status'        # Status filtering
    ],
    'composite_indexes': [
        ['asset_id', 'alarm_date'],      # Historical queries per asset
        ['location', 'alarm_status'],    # Location-based alarm queries
        ['alarm_status', 'alarm_date']   # Recent alarms
    ]
}
```

### Batch Processing Patterns

```python
def batch_transform_sensor_data(sensor_data_list, batch_size=100):
    """Transform multiple sensor records efficiently"""
    transformed_batches = []
    
    for i in range(0, len(sensor_data_list), batch_size):
        batch = sensor_data_list[i:i + batch_size]
        
        # Transform batch
        transformed_batch = []
        for sensor_data in batch:
            try:
                validated_data = validate_sensor_data(sensor_data)
                transformed = transform_sensor_data_to_arcgis(validated_data)
                transformed_batch.append(transformed)
            except Exception as e:
                # Log validation errors but continue processing
                logging.warning(f"Skipping invalid record: {str(e)}")
                continue
        
        transformed_batches.append(transformed_batch)
    
    return transformed_batches
```

## Error Handling & Data Recovery

### Validation Error Patterns

```python
class ValidationError(Exception):
    """Custom validation error with detailed information"""
    
    def __init__(self, field_name, value, expected_type, message=None):
        self.field_name = field_name
        self.value = value
        self.expected_type = expected_type
        self.message = message or f"Invalid {field_name}: {value}"
        super().__init__(self.message)

def handle_validation_errors(sensor_data, strict_mode=True):
    """Handle validation errors with recovery options"""
    errors = []
    recovered_data = sensor_data.copy()
    
    try:
        validate_sensor_data(recovered_data)
        return recovered_data, []
    except Exception as e:
        if strict_mode:
            raise e
        
        # Attempt recovery
        if "min_value must be less than max_value" in str(e):
            # Swap min/max if reversed
            if recovered_data.get('min_value', 0) > recovered_data.get('max_value', 0):
                recovered_data['min_value'], recovered_data['max_value'] = \
                    recovered_data['max_value'], recovered_data['min_value']
                errors.append("Swapped min_value and max_value")
        
        if "Invalid date format" in str(e):
            # Use current time as fallback
            recovered_data['alarm_date'] = datetime.now().isoformat() + 'Z'
            errors.append("Used current time for invalid alarm_date")
        
        return recovered_data, errors
```

---

**Schema Status**: ✅ Complete - Version 1.0 implemented with 20-field sensor data structure, comprehensive ArcGIS mapping, validation rules, and transformation patterns for historical data storage.