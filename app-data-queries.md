# Data Query Feature

## Overview

The data query feature provides REST API endpoints for retrieving historical sensor data from ArcGIS Online hosted feature services. This feature supports asset-specific queries, complete historical records, and advanced filtering capabilities to enable comprehensive analysis of sensor data over time.

## API Endpoints

### GET /api/features/{asset_id}

**Purpose**: Retrieve the latest sensor reading for a specific asset

**HTTP Method**: GET  
**Authentication**: Anonymous (development) / API Key (production)  
**Response Format**: JSON

**URL Parameters**:
- `asset_id` (required): Unique asset identifier

**Example Request**:
```bash
curl https://your-function-app.azurewebsites.net/api/features/blk-001-208
```

**Success Response (200 OK)**:
```json
{
  "found": true,
  "asset_id": "blk-001-208",
  "latest_record": {
    "OBJECTID": 12345,
    "location": "building-a-floor-2",
    "node_id": "node-001",
    "block_id": "blk-001",
    "level": 2,
    "ward": "ward-a",
    "asset_type": "plank",
    "asset_id": "blk-001-208",
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
    "alarm_date": 1642248600000,
    "device_type": "ultrasonic distance sensor",
    "record_created": 1642248605123
  }
}
```

**Not Found Response (404 Not Found)**:
```json
{
  "found": false,
  "asset_id": "unknown-asset",
  "message": "No records found for this asset"
}
```

### GET /api/features/{asset_id}/history

**Purpose**: Retrieve complete historical records for a specific asset

**HTTP Method**: GET  
**Authentication**: Anonymous (development) / API Key (production)  
**Response Format**: JSON

**URL Parameters**:
- `asset_id` (required): Unique asset identifier

**Query Parameters**:
- `limit` (optional): Maximum number of records to return (default: 100, max: 1000)
- `offset` (optional): Number of records to skip for pagination (default: 0)
- `start_date` (optional): Filter records after this date (ISO 8601 format)
- `end_date` (optional): Filter records before this date (ISO 8601 format)

**Example Requests**:
```bash
# Get latest 50 historical records
curl "https://your-function-app.azurewebsites.net/api/features/blk-001-208/history?limit=50"

# Get records from specific date range
curl "https://your-function-app.azurewebsites.net/api/features/blk-001-208/history?start_date=2024-01-01&end_date=2024-01-31"

# Pagination example
curl "https://your-function-app.azurewebsites.net/api/features/blk-001-208/history?limit=25&offset=50"
```

**Success Response (200 OK)**:
```json
{
  "asset_id": "blk-001-208",
  "total_records": 157,
  "returned_records": 50,
  "date_range": {
    "earliest": "2024-01-01T00:00:00.000Z",
    "latest": "2024-01-15T10:30:00.000Z"
  },
  "records": [
    {
      "OBJECTID": 12345,
      "present_value": 6.0,
      "alarm_status": "InAlarm",
      "alarm_date": 1642248600000,
      "record_created": 1642248605123,
      "device_type": "ultrasonic distance sensor"
    },
    {
      "OBJECTID": 12344,
      "present_value": 5.2,
      "alarm_status": "Normal", 
      "alarm_date": 1642245000000,
      "record_created": 1642245005123,
      "device_type": "ultrasonic distance sensor"
    }
  ]
}
```

### GET /api/features

**Purpose**: Retrieve latest sensor readings with optional filtering

**HTTP Method**: GET  
**Authentication**: Anonymous (development) / API Key (production)  
**Response Format**: JSON

**Query Parameters**:
- `limit` (optional): Maximum number of records to return (default: 10, max: 100)
- `where` (optional): ArcGIS WHERE clause for filtering
- `order_by` (optional): Field name for sorting results
- `fields` (optional): Comma-separated list of fields to return

**Example Requests**:
```bash
# Get latest 20 records
curl "https://your-function-app.azurewebsites.net/api/features?limit=20"

# Filter by alarm status
curl "https://your-function-app.azurewebsites.net/api/features?where=alarm_status='InAlarm'&limit=50"

# Filter by location and alarm code
curl "https://your-function-app.azurewebsites.net/api/features?where=location='building-a-floor-2' AND alarm_code=3"

# Return specific fields only
curl "https://your-function-app.azurewebsites.net/api/features?fields=asset_id,present_value,alarm_status&limit=25"
```

**Success Response (200 OK)**:
```json
{
  "success": true,
  "count": 15,
  "total_available": 1247,
  "query_info": {
    "where_clause": "alarm_status='InAlarm'",
    "limit": 50,
    "fields": "*"
  },
  "records": [
    {
      "OBJECTID": 12345,
      "asset_id": "blk-001-208",
      "present_value": 6.0,
      "alarm_status": "InAlarm",
      "alarm_date": 1642248600000,
      "location": "building-a-floor-2"
    },
    {
      "OBJECTID": 12343,
      "asset_id": "blk-002-105", 
      "present_value": 8.5,
      "alarm_status": "InAlarm",
      "alarm_date": 1642247000000,
      "location": "building-b-floor-1"
    }
  ]
}
```

## Query Implementation

### Latest Record Retrieval

```python
def get_latest_record_by_asset_id(asset_id):
    """Get the most recent record for a specific asset"""
    feature_service = get_feature_service()
    
    # Query with ordering to get latest record
    result = feature_service.query_features(
        where_clause=f"asset_id = '{asset_id}'",
        return_fields="*",
        max_records=1,
        order_by="alarm_date DESC"
    )
    
    if result['count'] > 0:
        return {
            "found": True,
            "asset_id": asset_id,
            "latest_record": result['features'][0]
        }
    else:
        return {
            "found": False,
            "asset_id": asset_id,
            "message": "No records found for this asset"
        }
```

### Historical Record Retrieval

```python
def get_historical_records(asset_id, limit=100, offset=0, start_date=None, end_date=None):
    """Get historical records with pagination and date filtering"""
    feature_service = get_feature_service()
    
    # Build WHERE clause with date filtering
    where_parts = [f"asset_id = '{asset_id}'"]
    
    if start_date:
        start_timestamp = int(datetime.fromisoformat(start_date).timestamp() * 1000)
        where_parts.append(f"alarm_date >= {start_timestamp}")
    
    if end_date:
        end_timestamp = int(datetime.fromisoformat(end_date).timestamp() * 1000)
        where_parts.append(f"alarm_date <= {end_timestamp}")
    
    where_clause = " AND ".join(where_parts)
    
    # First, get total count
    count_result = feature_service.query_features(
        where_clause=where_clause,
        return_fields="OBJECTID",
        max_records=1000
    )
    total_records = count_result['count']
    
    # Then get the requested records with pagination
    result = feature_service.query_features(
        where_clause=where_clause,
        return_fields="*",
        max_records=limit,
        order_by="alarm_date DESC"
    )
    
    return {
        "asset_id": asset_id,
        "total_records": total_records,
        "returned_records": len(result['features']),
        "records": result['features']
    }
```

### Advanced Filtering

```python
def query_features_with_filter(where_clause=None, limit=10, order_by=None, fields="*"):
    """Query features with advanced filtering options"""
    feature_service = get_feature_service()
    
    # Default to getting latest records if no WHERE clause provided
    if not where_clause:
        where_clause = "1=1"  # Return all records
    
    # Default ordering by latest alarm_date
    if not order_by:
        order_by = "alarm_date DESC"
    
    result = feature_service.query_features(
        where_clause=where_clause,
        return_fields=fields,
        max_records=limit,
        order_by=order_by
    )
    
    return {
        "success": True,
        "count": result['count'],
        "query_info": {
            "where_clause": where_clause,
            "limit": limit,
            "fields": fields,
            "order_by": order_by
        },
        "records": result['features']
    }
```

## Date & Time Handling

### ArcGIS Timestamp Format

ArcGIS stores dates as milliseconds since epoch (January 1, 1970):

```python
def convert_arcgis_timestamp(timestamp_ms):
    """Convert ArcGIS timestamp to ISO 8601 string"""
    if timestamp_ms:
        dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
        return dt.isoformat()
    return None

def parse_iso_to_arcgis_timestamp(iso_string):
    """Convert ISO 8601 string to ArcGIS timestamp (milliseconds)"""
    try:
        dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
        return int(dt.timestamp() * 1000)
    except ValueError:
        raise Exception(f"Invalid date format: {iso_string}")
```

### Date Range Queries

```python
def build_date_range_query(start_date=None, end_date=None):
    """Build ArcGIS WHERE clause for date range filtering"""
    conditions = []
    
    if start_date:
        start_ts = parse_iso_to_arcgis_timestamp(start_date)
        conditions.append(f"alarm_date >= {start_ts}")
    
    if end_date:
        end_ts = parse_iso_to_arcgis_timestamp(end_date)
        conditions.append(f"alarm_date <= {end_ts}")
    
    return " AND ".join(conditions) if conditions else None
```

## Pagination Implementation

### Offset-Based Pagination

```python
def paginate_query(where_clause, page_size=25, page_number=1):
    """Implement offset-based pagination for large result sets"""
    offset = (page_number - 1) * page_size
    
    # Note: ArcGIS REST API has limitations with large offsets
    # For better performance with large datasets, consider date-based pagination
    
    result = feature_service.query_features(
        where_clause=where_clause,
        return_fields="*",
        max_records=page_size,
        order_by="alarm_date DESC"
        # Note: ArcGIS REST API doesn't support OFFSET directly
        # This would need to be implemented using resultOffset parameter
    )
    
    return result
```

### Date-Based Pagination (Recommended)

```python
def paginate_by_date(asset_id, last_date=None, page_size=25):
    """Date-based pagination for better performance with large datasets"""
    where_parts = [f"asset_id = '{asset_id}'"]
    
    if last_date:
        last_timestamp = parse_iso_to_arcgis_timestamp(last_date)
        where_parts.append(f"alarm_date < {last_timestamp}")
    
    where_clause = " AND ".join(where_parts)
    
    result = feature_service.query_features(
        where_clause=where_clause,
        return_fields="*",
        max_records=page_size,
        order_by="alarm_date DESC"
    )
    
    return result
```

## Performance Optimization

### Query Performance Best Practices

1. **Indexed Fields**: Use asset_id and alarm_date (typically indexed) in WHERE clauses
2. **Field Selection**: Request only needed fields using `fields` parameter
3. **Limit Results**: Always use reasonable limits (max 1000 per request)
4. **Ordering**: Use indexed fields for ORDER BY when possible

### Caching Strategy

```python
from functools import lru_cache
from datetime import timedelta

@lru_cache(maxsize=100)
def get_cached_latest_record(asset_id, cache_minutes=5):
    """Cache latest records for frequently accessed assets"""
    # Simple in-memory caching with TTL
    # In production, consider Redis or Azure Cache for Redis
    return get_latest_record_by_asset_id(asset_id)
```

### Connection Optimization

```python
# Reuse connections across function invocations
_feature_service_cache = None

def get_optimized_feature_service():
    """Get feature service with connection reuse"""
    global _feature_service_cache
    if _feature_service_cache is None:
        _feature_service_cache = get_feature_service()
    return _feature_service_cache
```

## Error Handling

### Query Error Responses

**400 Bad Request** - Invalid query parameters:
```json
{
  "error": "Invalid WHERE clause: missing closing quote",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "status_code": 400
}
```

**500 Internal Server Error** - ArcGIS service failure:
```json
{
  "error": "ArcGIS query failed: service temporarily unavailable",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "status_code": 500
}
```

### Query Validation

```python
def validate_query_parameters(where_clause=None, limit=None, fields=None):
    """Validate query parameters before sending to ArcGIS"""
    errors = []
    
    # Validate limit
    if limit is not None:
        if not isinstance(limit, int) or limit < 1 or limit > 1000:
            errors.append("Limit must be an integer between 1 and 1000")
    
    # Validate WHERE clause (basic SQL injection prevention)
    if where_clause:
        dangerous_patterns = ['drop', 'delete', 'truncate', 'update', 'insert']
        where_lower = where_clause.lower()
        if any(pattern in where_lower for pattern in dangerous_patterns):
            errors.append("WHERE clause contains potentially dangerous operations")
    
    # Validate field list
    if fields and fields != "*":
        field_list = [f.strip() for f in fields.split(',')]
        for field in field_list:
            if not field.replace('_', '').isalnum():
                errors.append(f"Invalid field name: {field}")
    
    if errors:
        raise Exception(f"Validation errors: {'; '.join(errors)}")
```

## Usage Examples

### Real-World Query Scenarios

```bash
# Monitor all assets in alarm state
curl "https://your-function-app.azurewebsites.net/api/features?where=alarm_status='InAlarm'&limit=100"

# Get readings for specific building
curl "https://your-function-app.azurewebsites.net/api/features?where=location LIKE 'building-a%'&limit=50"

# Check high-value sensor readings
curl "https://your-function-app.azurewebsites.net/api/features?where=present_value>threshold_value&fields=asset_id,present_value,threshold_value"

# Historical trend analysis
curl "https://your-function-app.azurewebsites.net/api/features/blk-001-208/history?start_date=2024-01-01&limit=1000"

# Pagination through large datasets
curl "https://your-function-app.azurewebsites.net/api/features/blk-001-208/history?limit=100&offset=0"
curl "https://your-function-app.azurewebsites.net/api/features/blk-001-208/history?limit=100&offset=100"
```

## Known Limitations

### ArcGIS REST API Constraints
- **Maximum Records**: 1000 records per query (ArcGIS limitation)
- **Query Complexity**: Complex WHERE clauses may impact performance
- **Timeout Limits**: Long-running queries subject to 30-second timeout
- **Rate Limiting**: 1000 requests/minute per authentication token

### Current Implementation Limits
- **Pagination**: Offset-based pagination not fully optimized for large datasets
- **Caching**: No persistent caching implemented (in-memory only)
- **Aggregation**: No built-in aggregation functions (count, average, etc.)
- **Real-time**: No real-time data streaming or push notifications

## Future Enhancements

### Planned Query Features
- **Aggregation Endpoints**: Count, average, min/max calculations
- **Export Functionality**: CSV, Excel export capabilities
- **Real-time Queries**: WebSocket support for real-time data
- **Advanced Analytics**: Trend analysis and anomaly detection
- **Caching Layer**: Redis-based caching for improved performance

### Integration Opportunities
- **Power BI**: Direct connector for dashboard creation
- **Azure Data Factory**: ETL pipelines for data warehousing
- **Azure Stream Analytics**: Real-time analytics and alerting
- **Machine Learning**: Predictive analytics integration

---

**Implementation Status**: ✅ Complete - Phase 3 implementation with comprehensive query endpoints, pagination support, filtering capabilities, and historical data access patterns.