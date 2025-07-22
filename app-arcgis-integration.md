# ArcGIS Integration Feature

## Overview

The ArcGIS integration feature provides connectivity between Azure Functions and ArcGIS Online hosted feature services. This feature implements token-based authentication, feature service operations, and comprehensive error handling using Python's built-in urllib library for maximum reliability and performance.

## ArcGIS Online Configuration

### Service Details
- **Service Name**: SensorDataService
- **Service ID**: `f4682a40e60847fe8289408e73933b82`
- **Table Name**: SensorReadings  
- **Service URL**: `https://services-eu1.arcgis.com/veDTgAL7B9EBogdG/arcgis/rest/services/SensorDataService/FeatureServer`
- **Layer Index**: 0 (first table in the service)

### Authentication Requirements
- **ArcGIS URL**: `https://www.arcgis.com`
- **Authentication Method**: Username/Password with token generation
- **Token Duration**: 60 minutes with 5-minute buffer for refresh
- **Credentials Storage**: Azure Function App settings (environment variables)

## Authentication Implementation

### Token Management

The integration uses a robust token management system that handles authentication, token caching, and automatic refresh:

```python
class ArcGISRestClient:
    def __init__(self, org_url, username, password):
        self.org_url = org_url.rstrip('/')
        self.username = username
        self.password = password
        self.token = None
        self.token_expires = None
        
    def get_token(self, force_refresh=False):
        """Generate or refresh ArcGIS authentication token"""
        if not force_refresh and self.token and self.token_expires > datetime.now():
            return self.token
            
        token_url = f"{self.org_url}/sharing/rest/generateToken"
        
        # ArcGIS-compliant token request parameters
        params = {
            'username': self.username,
            'password': self.password,
            'client': 'requestip',  # Critical for Azure Functions
            'f': 'json',
            'expiration': 60  # 60 minutes
        }
        
        data = urllib.parse.urlencode(params).encode('utf-8')
        req = urllib.request.Request(token_url, data=data, method='POST')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        
        response = urllib.request.urlopen(req, timeout=30)
        result = json.loads(response.read().decode('utf-8'))
        
        if 'error' in result:
            raise Exception(f"Authentication failed: {result['error']}")
            
        self.token = result['token']
        self.token_expires = datetime.now() + timedelta(minutes=55)  # 5-minute buffer
        return self.token
```

### Connection Validation

```python
def validate_connection(self):
    """Test ArcGIS Online connectivity and permissions"""
    portal_url = f"{self.org_url}/sharing/rest/portals/self"
    
    params = {
        'token': self.get_token(),
        'f': 'json'
    }
    
    query_string = urllib.parse.urlencode(params)
    url = f"{portal_url}?{query_string}"
    
    req = urllib.request.Request(url)
    response = urllib.request.urlopen(req, timeout=30)
    result = json.loads(response.read().decode('utf-8'))
    
    return {
        'user': result.get('user', {}).get('username'),
        'org': result.get('name'),
        'status': 'healthy' if 'error' not in result else 'unhealthy'
    }
```

## Feature Service Operations

### Service URL Construction

Direct URL construction eliminates complex service discovery logic:

```python
class ArcGISFeatureService:
    def __init__(self, rest_client, service_id, layer_index=0):
        self.client = rest_client
        self.service_id = service_id
        self.layer_index = layer_index
        
        # Direct service URL construction - no discovery needed
        self.service_url = f"https://services-eu1.arcgis.com/veDTgAL7B9EBogdG/arcgis/rest/services/SensorDataService/FeatureServer"
        self.layer_url = f"{self.service_url}/{layer_index}"
```

### Add Features Operation

Historical data ingestion using ArcGIS REST API:

```python
def add_features(self, features):
    """Add new features to the hosted feature service"""
    url = f"{self.layer_url}/addFeatures"
    
    # Convert to ArcGIS feature format
    arcgis_features = []
    for feature in features:
        arcgis_features.append({
            "attributes": self._convert_to_arcgis_attributes(feature)
        })
    
    # ArcGIS REST API parameters
    params = {
        'features': json.dumps(arcgis_features),
        'rollbackOnFailure': 'true',
        'token': self.client.get_token(),
        'f': 'json'
    }
    
    data = urllib.parse.urlencode(params).encode('utf-8')
    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    
    response = urllib.request.urlopen(req, timeout=30)
    result = json.loads(response.read().decode('utf-8'))
    
    if 'addResults' in result:
        return self._process_add_results(result['addResults'])
    else:
        raise Exception(f"Add features failed: {result}")
```

### Query Features Operation

Historical data retrieval with filtering and sorting:

```python
def query_features(self, where_clause="1=1", return_fields="*", max_records=1000, order_by=None):
    """Query features from the hosted feature service"""
    url = f"{self.layer_url}/query"
    
    params = {
        'where': where_clause,
        'outFields': return_fields,
        'resultRecordCount': max_records,
        'returnGeometry': 'false',
        'token': self.client.get_token(),
        'f': 'json'
    }
    
    # Add ordering for historical queries
    if order_by:
        params['orderByFields'] = order_by
    
    query_string = urllib.parse.urlencode(params)
    full_url = f"{url}?{query_string}"
    
    req = urllib.request.Request(full_url)
    response = urllib.request.urlopen(req, timeout=30)
    result = json.loads(response.read().decode('utf-8'))
    
    if 'features' in result:
        return {
            'success': True,
            'count': len(result['features']),
            'features': [f['attributes'] for f in result['features']]
        }
    else:
        raise Exception(f"Query failed: {result}")
```

## Data Transformation

### Field Mapping Implementation

JSON sensor data fields mapped to ArcGIS table columns:

```python
def _convert_to_arcgis_attributes(self, sensor_data):
    """Convert sensor data dictionary to ArcGIS attributes format"""
    
    # Field mappings from JSON to ArcGIS table
    field_mappings = {
        'location': 'location',
        'node_id': 'node_id', 
        'block': 'block_id',        # Special mapping: JSON 'block' → ArcGIS 'block_id'
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
    
    attributes = {}
    
    for json_field, arcgis_field in field_mappings.items():
        if json_field in sensor_data:
            value = sensor_data[json_field]
            
            # Date conversion: ISO string to ArcGIS timestamp (milliseconds)
            if json_field == 'alarm_date' and isinstance(value, str):
                try:
                    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    value = int(dt.timestamp() * 1000)  # Convert to milliseconds
                except ValueError:
                    # Fallback to current time if date parsing fails
                    value = int(datetime.now().timestamp() * 1000)
            
            attributes[arcgis_field] = value
    
    return attributes
```

### Processing Timestamp Addition

Each record includes processing metadata for audit purposes:

```python
# Add processing timestamp for audit trail
processing_time = datetime.now()
attributes['record_created'] = int(processing_time.timestamp() * 1000)
```

## Error Handling & Resilience

### Authentication Error Handling

```python
def _handle_auth_error(self, e):
    """Handle ArcGIS authentication failures"""
    error_msg = str(e).lower()
    
    if 'invalid username or password' in error_msg:
        return "Invalid ArcGIS credentials"
    elif 'token required' in error_msg:
        return "ArcGIS token generation failed"
    elif 'timeout' in error_msg:
        return "ArcGIS authentication timeout"
    else:
        return f"ArcGIS authentication error: {str(e)}"
```

### Feature Service Error Handling

```python
def _handle_service_error(self, result):
    """Handle ArcGIS feature service operation errors"""
    if 'error' in result:
        error = result['error']
        error_code = error.get('code', 'unknown')
        error_msg = error.get('message', 'Unknown error')
        
        if error_code == 400:
            return f"Invalid request parameters: {error_msg}"
        elif error_code == 403:
            return f"Access denied: {error_msg}"
        elif error_code == 500:
            return f"ArcGIS server error: {error_msg}"
        else:
            return f"ArcGIS error {error_code}: {error_msg}"
    
    return "Unknown ArcGIS service error"
```

### Connection Timeout Handling

```python
def _make_request_with_retry(self, url, data=None, max_retries=2):
    """Make HTTP request with retry logic for transient failures"""
    for attempt in range(max_retries + 1):
        try:
            if data:
                req = urllib.request.Request(url, data=data, method='POST')
                req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            else:
                req = urllib.request.Request(url)
            
            response = urllib.request.urlopen(req, timeout=30)
            return json.loads(response.read().decode('utf-8'))
            
        except urllib.error.URLError as e:
            if attempt < max_retries and 'timeout' in str(e).lower():
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            raise Exception(f"HTTP request failed: {str(e)}")
        except Exception as e:
            if attempt < max_retries:
                time.sleep(2 ** attempt)
                continue
            raise e
```

## Performance Optimization

### Connection Reuse Strategy

Global connection objects minimize initialization overhead:

```python
# Global variables for connection reuse across function invocations
_rest_client = None
_feature_service = None

def get_rest_client():
    """Get or create ArcGIS REST client with connection reuse"""
    global _rest_client
    if _rest_client is None:
        _rest_client = ArcGISRestClient(
            org_url=os.environ.get('ARCGIS_URL', 'https://www.arcgis.com'),
            username=os.environ['ARCGIS_USERNAME'],
            password=os.environ['ARCGIS_PASSWORD']
        )
    return _rest_client

def get_feature_service():
    """Get or create feature service client with connection reuse"""
    global _feature_service
    if _feature_service is None:
        client = get_rest_client()
        _feature_service = ArcGISFeatureService(
            rest_client=client,
            service_id=os.environ['FEATURE_SERVICE_ID'],
            layer_index=int(os.environ.get('FEATURE_LAYER_INDEX', '0'))
        )
    return _feature_service
```

### Token Caching Strategy

Tokens are cached and automatically refreshed to minimize authentication overhead:

- **Token Duration**: 60 minutes from ArcGIS
- **Refresh Buffer**: 5-minute buffer before expiration
- **Automatic Refresh**: Transparent token refresh on expiration
- **Error Recovery**: Force refresh on authentication failures

## Configuration Management

### Environment Variables

Required Azure Function App settings:

| Variable | Description | Example |
|----------|-------------|---------|
| ARCGIS_URL | ArcGIS Online organization URL | https://www.arcgis.com |
| ARCGIS_USERNAME | ArcGIS Online username | your-username |
| ARCGIS_PASSWORD | ArcGIS Online password | your-password |
| FEATURE_SERVICE_ID | Hosted feature service ID | f4682a40e60847fe8289408e73933b82 |
| FEATURE_LAYER_INDEX | Layer index within service | 0 |

### Configuration Validation

```python
def validate_configuration():
    """Validate all required ArcGIS configuration is present"""
    required_vars = [
        'ARCGIS_USERNAME',
        'ARCGIS_PASSWORD', 
        'FEATURE_SERVICE_ID'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise Exception(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    return True
```

## Known Compatibility Issues

### ArcGIS REST API Specific Requirements

1. **Token Generation Parameters**:
   - Must use `'client': 'requestip'` parameter for Azure Functions
   - Expiration must be specified in minutes
   - Content-Type must be `application/x-www-form-urlencoded`

2. **Feature Service URLs**:
   - Service URLs must use HTTPS
   - European services use `services-eu1.arcgis.com` domain
   - Layer index is zero-based (0, 1, 2, ...)

3. **Date Handling**:
   - ArcGIS expects timestamps in milliseconds since epoch
   - ISO 8601 strings must be converted to numeric timestamps
   - Date fields cannot be null or empty strings

### Python urllib Specific Patterns

1. **Request Construction**:
   - POST data must be URL-encoded and converted to bytes
   - Headers must be set explicitly for content type
   - Timeout must be specified to prevent hanging

2. **Response Handling**:
   - Response must be decoded from bytes to string
   - JSON parsing must handle potential encoding issues
   - Error responses may not include standard HTTP error codes

## Future Enhancements

### Planned Improvements

1. **Batch Operations**: Support for multiple features per request
2. **Connection Pooling**: Advanced connection management for high throughput
3. **Caching Layer**: Feature metadata caching for improved performance
4. **Health Metrics**: Detailed connection health and performance metrics

### Integration Opportunities

1. **Azure Key Vault**: Secure credential storage and rotation
2. **Application Insights**: Enhanced monitoring and alerting
3. **Azure Service Bus**: Asynchronous processing for high-volume scenarios
4. **Power BI**: Direct integration for real-time dashboards

---

**Implementation Status**: ✅ Complete - Phase 2 & 3 implementation with robust authentication, feature service operations, and comprehensive error handling using urllib-based REST API integration.