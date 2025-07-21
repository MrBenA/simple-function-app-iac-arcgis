import azure.functions as func
import logging
import json
import os
from datetime import datetime

# Test requests import
try:
    import requests
    REQUESTS_AVAILABLE = True
    logging.info("Requests library imported successfully")
except ImportError as e:
    REQUESTS_AVAILABLE = False
    logging.error(f"Requests import failed: {e}")

# Always available - Python built-in
import urllib.request
import urllib.parse
from urllib.error import URLError
from datetime import datetime, timedelta
URLLIB_AVAILABLE = True

class ArcGISRestClient:
    """Lightweight ArcGIS REST API client using urllib"""
    
    def __init__(self, org_url, username, password):
        self.org_url = org_url.rstrip('/')
        self.username = username
        self.password = password
        self.token = None
        self.token_expires = None
    
    def get_token(self, force_refresh=False):
        """Get or refresh authentication token using urllib POST"""
        # Check if we have a valid token
        if not force_refresh and self.token and self.token_expires > datetime.utcnow():
            return self.token
        
        try:
            # Prepare token request
            token_url = f"{self.org_url}/sharing/rest/generateToken"
            data = {
                'username': self.username,
                'password': self.password,
                'client': 'requestip',
                'f': 'json',
                'expiration': 60,  # 60 minutes
                'referer': 'https://www.arcgis.com'  # Add referer for feature service operations
            }
            
            # Encode data for POST request
            data_encoded = urllib.parse.urlencode(data).encode('utf-8')
            
            # Create POST request
            request = urllib.request.Request(
                token_url,
                data=data_encoded,
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'User-Agent': 'Azure-Functions-ArcGIS-Client/1.0'
                }
            )
            
            # Make the request
            with urllib.request.urlopen(request, timeout=10) as response:
                if response.status == 200:
                    content = response.read()
                    result = json.loads(content.decode('utf-8'))
                    
                    if 'error' in result:
                        raise Exception(f"Authentication failed: {result['error']}")
                    
                    if 'token' not in result:
                        raise Exception("No token returned in response")
                    
                    self.token = result['token']
                    self.token_expires = datetime.utcnow() + timedelta(minutes=55)  # 5min buffer
                    
                    logging.info(f"Successfully obtained ArcGIS token, expires: {self.token_expires}")
                    return self.token
                else:
                    raise Exception(f"HTTP {response.status}: {response.reason}")
                    
        except URLError as e:
            logging.error(f"Failed to get ArcGIS token (URLError): {str(e)}")
            raise Exception(f"Network error: {str(e)}")
        except Exception as e:
            logging.error(f"Failed to get ArcGIS token: {str(e)}")
            raise
    
    def test_connection(self):
        """Test ArcGIS Online connectivity using portal info"""
        try:
            # Get valid token first
            token = self.get_token()
            
            # Test with portal info request  
            portal_url = f"{self.org_url}/sharing/rest/portals/self"
            params = {
                'token': token,
                'f': 'json'
            }
            
            # Encode parameters for GET request
            query_string = urllib.parse.urlencode(params)
            full_url = f"{portal_url}?{query_string}"
            
            # Create GET request
            request = urllib.request.Request(
                full_url,
                headers={'User-Agent': 'Azure-Functions-ArcGIS-Client/1.0'}
            )
            
            # Make the request
            with urllib.request.urlopen(request, timeout=10) as response:
                if response.status == 200:
                    content = response.read()
                    result = json.loads(content.decode('utf-8'))
                    
                    if 'error' in result:
                        raise Exception(f"Portal info failed: {result['error']}")
                    
                    return {
                        'success': True,
                        'org_name': result.get('name', 'Unknown'),
                        'org_id': result.get('id', 'Unknown'),
                        'user': result.get('user', {}).get('username', 'Unknown'),
                        'portal_url': self.org_url
                    }
                else:
                    raise Exception(f"HTTP {response.status}: {response.reason}")
                    
        except Exception as e:
            logging.error(f"ArcGIS connection test failed: {str(e)}")
            return {
                'success': False, 
                'error': str(e)
            }

class ArcGISFeatureService:
    """ArcGIS Feature Service operations for historical sensor data"""
    
    def __init__(self, rest_client, service_id, layer_index=0):
        self.client = rest_client
        self.service_id = service_id
        self.layer_index = layer_index
        # For hosted services, we'll use dynamic service URL discovery
        # This will be set when we first access the service
        self.service_url = None
        self.layer_url = None
        self.layer_index = layer_index
    
    def _get_service_url(self):
        """Dynamically discover the correct service URL from the service item"""
        if self.service_url is None:
            try:
                # Get service item details using the service ID
                token = self.client.get_token()
                item_url = f"{self.client.org_url}/sharing/rest/content/items/{self.service_id}"
                params = {
                    'token': token,
                    'f': 'json'
                }
                
                query_string = urllib.parse.urlencode(params)
                full_url = f"{item_url}?{query_string}"
                
                request = urllib.request.Request(
                    full_url,
                    headers={'User-Agent': 'Azure-Functions-ArcGIS-Client/1.0'}
                )
                
                with urllib.request.urlopen(request, timeout=10) as response:
                    if response.status == 200:
                        content = response.read()
                        result = json.loads(content.decode('utf-8'))
                        
                        if 'url' in result:
                            self.service_url = result['url']
                            self.layer_url = f"{self.service_url}/{self.layer_index}"
                            logging.info(f"Discovered service URL: {self.service_url}")
                            return
                
                # Fallback to constructed URL if discovery fails
                raise Exception("Could not discover service URL")
                
            except Exception as e:
                logging.warning(f"Service URL discovery failed: {str(e)}, using fallback")
                # Fallback to hardcoded service name
                service_name = "SensorDataService"
                self.service_url = f"https://services-eu1.arcgis.com/veDTgAL7B9EBogdG/arcgis/rest/services/{service_name}/FeatureServer"
                self.layer_url = f"{self.service_url}/{self.layer_index}"
        
        return self.layer_url
    
    def add_features(self, features):
        """Add new historical features to the service"""
        try:
            # Ensure service URL is discovered
            layer_url = self._get_service_url()
            url = f"{layer_url}/addFeatures"
            
            # Convert features to ArcGIS format
            arcgis_features = []
            for feature in features:
                arcgis_features.append({
                    "attributes": self._convert_to_arcgis_attributes(feature)
                })
            
            # Prepare POST data
            data = {
                'features': json.dumps(arcgis_features),
                'rollbackOnFailure': 'true'
            }
            
            # Get token and add to data
            token = self.client.get_token()
            data['token'] = token
            data['f'] = 'json'
            
            # Debug logging
            logging.info(f"Using token for feature service operation: {token[:20]}...")
            logging.info(f"Feature service URL: {url}")
            
            # Encode data for POST request
            data_encoded = urllib.parse.urlencode(data).encode('utf-8')
            
            # Create POST request
            request = urllib.request.Request(
                url,
                data=data_encoded,
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'User-Agent': 'Azure-Functions-ArcGIS-Client/1.0'
                }
            )
            
            # Make the request
            with urllib.request.urlopen(request, timeout=30) as response:
                if response.status == 200:
                    content = response.read()
                    result = json.loads(content.decode('utf-8'))
                    
                    if 'error' in result:
                        raise Exception(f"Add features failed: {result['error']}")
                    
                    if 'addResults' in result:
                        success_count = len([r for r in result['addResults'] if r.get('success')])
                        failed_count = len([r for r in result['addResults'] if not r.get('success')])
                        
                        return {
                            'success': True,
                            'added_count': success_count,
                            'failed_count': failed_count,
                            'results': result['addResults']
                        }
                    else:
                        raise Exception(f"Unexpected response format: {result}")
                else:
                    raise Exception(f"HTTP {response.status}: {response.reason}")
                    
        except URLError as e:
            logging.error(f"Feature service add failed (URLError): {str(e)}")
            raise Exception(f"Network error: {str(e)}")
        except Exception as e:
            logging.error(f"Feature service add failed: {str(e)}")
            raise
    
    def query_features(self, where_clause="1=1", return_fields="*", max_records=1000, order_by=None):
        """Query features from the service"""
        try:
            # Ensure service URL is discovered
            layer_url = self._get_service_url()
            url = f"{layer_url}/query"
            
            # Prepare query parameters
            params = {
                'where': where_clause,
                'outFields': return_fields,
                'resultRecordCount': max_records,
                'returnGeometry': 'false',
                'f': 'json'
            }
            
            # Add ordering if specified
            if order_by:
                params['orderByFields'] = order_by
            
            # Get token and add to params
            token = self.client.get_token()
            params['token'] = token
            
            # Encode parameters for GET request
            query_string = urllib.parse.urlencode(params)
            full_url = f"{url}?{query_string}"
            
            # Create GET request
            request = urllib.request.Request(
                full_url,
                headers={'User-Agent': 'Azure-Functions-ArcGIS-Client/1.0'}
            )
            
            # Make the request
            with urllib.request.urlopen(request, timeout=30) as response:
                if response.status == 200:
                    content = response.read()
                    result = json.loads(content.decode('utf-8'))
                    
                    if 'error' in result:
                        raise Exception(f"Query failed: {result['error']}")
                    
                    if 'features' in result:
                        return {
                            'success': True,
                            'count': len(result['features']),
                            'features': [f['attributes'] for f in result['features']]
                        }
                    else:
                        raise Exception(f"Unexpected response format: {result}")
                else:
                    raise Exception(f"HTTP {response.status}: {response.reason}")
                    
        except URLError as e:
            logging.error(f"Feature service query failed (URLError): {str(e)}")
            raise Exception(f"Network error: {str(e)}")
        except Exception as e:
            logging.error(f"Feature service query failed: {str(e)}")
            raise
    
    def _convert_to_arcgis_attributes(self, sensor_data):
        """Convert sensor data to ArcGIS attributes format with field mapping"""
        attributes = {}
        
        # Field mapping (sensor JSON field -> ArcGIS table field)
        field_mappings = {
            'location': 'location',
            'node_id': 'node_id',
            'block': 'block_id',           # Note: JSON has 'block', table has 'block_id'
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
        
        for json_field, arcgis_field in field_mappings.items():
            if json_field in sensor_data:
                value = sensor_data[json_field]
                
                # Handle date conversion (ISO string → ArcGIS timestamp in milliseconds)
                if json_field == 'alarm_date' and isinstance(value, str):
                    try:
                        # Parse ISO string and convert to milliseconds since epoch
                        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        value = int(dt.timestamp() * 1000)
                    except ValueError as e:
                        logging.warning(f"Invalid date format in alarm_date: {value}, error: {e}")
                        # Use current time as fallback
                        value = int(datetime.utcnow().timestamp() * 1000)
                
                attributes[arcgis_field] = value
        
        return attributes

# Sensor Data Validation
class SensorData:
    """Sensor data validation and structure"""
    
    def __init__(self, data):
        self.data = data
        self._validate()
    
    def _validate(self):
        """Validate required fields and data types"""
        required_fields = {
            'asset_id': str,
            'present_value': (int, float),
            'alarm_date': str,
            'device_type': str
        }
        
        # Check required fields
        for field, expected_type in required_fields.items():
            if field not in self.data:
                raise ValueError(f"Missing required field: {field}")
            
            if not isinstance(self.data[field], expected_type):
                raise ValueError(f"Field '{field}' must be of type {expected_type.__name__}")
        
        # Validate alarm_date format
        try:
            datetime.fromisoformat(self.data['alarm_date'].replace('Z', '+00:00'))
        except ValueError:
            raise ValueError(f"Field 'alarm_date' must be in ISO format (e.g., '2024-01-15T10:30:00.000Z')")
    
    def to_dict(self):
        """Return validated data as dictionary"""
        return self.data

def validate_sensor_data(req_body):
    """Validate sensor data from request body"""
    if not req_body:
        raise ValueError("Request body is empty")
    
    sensor_data = SensorData(req_body)
    return sensor_data.to_dict()

# Global REST client and feature service instances
_rest_client = None
_feature_service = None

def get_rest_client():
    """Get or create ArcGIS REST client"""
    global _rest_client
    if _rest_client is None:
        _rest_client = ArcGISRestClient(
            org_url=os.environ.get('ARCGIS_URL', 'https://www.arcgis.com'),
            username=os.environ.get('ARCGIS_USERNAME', ''),
            password=os.environ.get('ARCGIS_PASSWORD', '')
        )
    return _rest_client

def get_feature_service():
    """Get or create ArcGIS Feature Service client"""
    global _feature_service
    if _feature_service is None:
        rest_client = get_rest_client()
        service_id = os.environ.get('FEATURE_SERVICE_ID', 'f4682a40e60847fe8289408e73933b82')
        layer_index = int(os.environ.get('FEATURE_LAYER_INDEX', '0'))
        _feature_service = ArcGISFeatureService(rest_client, service_id, layer_index)
    return _feature_service

app = func.FunctionApp()

@app.route(route="health", auth_level=func.AuthLevel.ANONYMOUS)
def health(req: func.HttpRequest) -> func.HttpResponse:
    """Simple health check endpoint"""
    logging.info('Health check requested')
    
    health_data = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0-arcgis-rest-api",
        "python_version": "3.11",
        "requests_available": REQUESTS_AVAILABLE,
        "urllib_available": URLLIB_AVAILABLE,
        "dependencies": {
            "urllib": "available",
            "arcgis_online": "unknown"
        }
    }
    
    # Test ArcGIS connectivity if credentials are provided
    try:
        username = os.environ.get('ARCGIS_USERNAME', '')
        password = os.environ.get('ARCGIS_PASSWORD', '')
        
        if username and password:
            rest_client = get_rest_client()
            connection_test = rest_client.test_connection()
            
            if connection_test['success']:
                health_data["dependencies"]["arcgis_online"] = "healthy"
                health_data["arcgis_org"] = connection_test['org_name']
                health_data["arcgis_user"] = connection_test['user']
                health_data["token_expires"] = rest_client.token_expires.isoformat() if rest_client.token_expires else None
            else:
                health_data["dependencies"]["arcgis_online"] = f"unhealthy: {connection_test['error']}"
                health_data["status"] = "degraded"
        else:
            health_data["dependencies"]["arcgis_online"] = "no credentials configured"
    
    except Exception as e:
        logging.error(f"Health check ArcGIS test failed: {str(e)}")
        health_data["dependencies"]["arcgis_online"] = f"error: {str(e)}"
        health_data["status"] = "degraded"
    
    # Set appropriate status code
    status_code = 200 if health_data["status"] == "healthy" else 503
    
    return func.HttpResponse(
        json.dumps(health_data),
        status_code=status_code,
        mimetype="application/json"
    )

@app.route(route="test", auth_level=func.AuthLevel.ANONYMOUS)
def test(req: func.HttpRequest) -> func.HttpResponse:
    """Simple test endpoint"""
    logging.info('Test endpoint requested')
    
    return func.HttpResponse(
        "Hello from Azure Functions! Minimal version restored.",
        status_code=200
    )

@app.route(route="hello", auth_level=func.AuthLevel.ANONYMOUS)
def hello(req: func.HttpRequest) -> func.HttpResponse:
    """Hello world endpoint with optional name parameter"""
    logging.info('Hello endpoint requested')
    
    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name') if req_body else None
    
    if name:
        response_text = f"Hello, {name}! Minimal version confirmed working."
    else:
        response_text = "Hello, World! Minimal version confirmed working."
    
    return func.HttpResponse(
        response_text,
        status_code=200
    )

@app.route(route="requests-test", auth_level=func.AuthLevel.ANONYMOUS)
def requests_test(req: func.HttpRequest) -> func.HttpResponse:
    """Test requests library with simple HTTP call"""
    logging.info('Requests test requested')
    
    if not REQUESTS_AVAILABLE:
        return func.HttpResponse(
            json.dumps({
                "error": "Requests library not available",
                "timestamp": datetime.utcnow().isoformat()
            }),
            status_code=500,
            mimetype="application/json"
        )
    
    try:
        # Simple HTTP test to a reliable endpoint
        response = requests.get('https://httpbin.org/json', timeout=10)
        response.raise_for_status()
        
        test_data = response.json()
        
        return func.HttpResponse(
            json.dumps({
                "status": "success",
                "message": "Requests library working perfectly",
                "test_url": "https://httpbin.org/json",
                "response_status": response.status_code,
                "response_data": test_data,
                "python_version": "3.11",
                "requests_version": getattr(requests, '__version__', 'unknown'),
                "timestamp": datetime.utcnow().isoformat()
            }),
            status_code=200,
            mimetype="application/json"
        )
    
    except Exception as e:
        logging.error(f"Requests test failed: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="urllib-test", auth_level=func.AuthLevel.ANONYMOUS)
def urllib_test(req: func.HttpRequest) -> func.HttpResponse:
    """Test urllib (built-in) with simple HTTP call"""
    logging.info('urllib test requested')
    
    try:
        # Simple HTTP test using urllib
        with urllib.request.urlopen('https://httpbin.org/json', timeout=10) as response:
            if response.status == 200:
                content = response.read()
                test_data = json.loads(content.decode('utf-8'))
                
                return func.HttpResponse(
                    json.dumps({
                        "status": "success",
                        "message": "urllib (built-in) working perfectly",
                        "test_url": "https://httpbin.org/json",
                        "response_status": response.status,
                        "response_data": test_data,
                        "python_version": "3.11",
                        "http_library": "urllib (built-in)",
                        "timestamp": datetime.utcnow().isoformat()
                    }),
                    status_code=200,
                    mimetype="application/json"
                )
            else:
                raise Exception(f"HTTP {response.status}")
                
    except URLError as e:
        logging.error(f"urllib test failed (URLError): {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "status": "failed",
                "error": f"URLError: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }),
            status_code=500,
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"urllib test failed: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="arcgis-test", auth_level=func.AuthLevel.ANONYMOUS)
def arcgis_test(req: func.HttpRequest) -> func.HttpResponse:
    """Test ArcGIS REST API connectivity using urllib"""
    logging.info('ArcGIS REST API test requested')
    
    try:
        username = os.environ.get('ARCGIS_USERNAME', '')
        password = os.environ.get('ARCGIS_PASSWORD', '')
        
        if not username or not password:
            return func.HttpResponse(
                json.dumps({
                    "error": "ArcGIS credentials not configured",
                    "help": "Set ARCGIS_USERNAME and ARCGIS_PASSWORD environment variables",
                    "timestamp": datetime.utcnow().isoformat()
                }),
                status_code=400,
                mimetype="application/json"
            )
        
        # Test connection
        rest_client = get_rest_client()
        connection_test = rest_client.test_connection()
        
        if connection_test['success']:
            response_data = {
                "status": "success",
                "message": "ArcGIS REST API connection successful using urllib",
                "org_name": connection_test['org_name'],
                "org_id": connection_test['org_id'],
                "user": connection_test['user'],
                "portal_url": connection_test['portal_url'],
                "token_expires": rest_client.token_expires.isoformat() if rest_client.token_expires else None,
                "approach": "urllib-based REST API (zero external dependencies)",
                "python_version": "3.11",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return func.HttpResponse(
                json.dumps(response_data),
                status_code=200,
                mimetype="application/json"
            )
        else:
            return func.HttpResponse(
                json.dumps({
                    "status": "failed",
                    "error": connection_test['error'],
                    "timestamp": datetime.utcnow().isoformat()
                }),
                status_code=503,
                mimetype="application/json"
            )
    
    except Exception as e:
        logging.error(f"ArcGIS test failed: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "status": "error", 
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="sensor-data", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
def sensor_data(req: func.HttpRequest) -> func.HttpResponse:
    """Process sensor data and create historical records in ArcGIS"""
    logging.info('Sensor data POST requested')
    
    try:
        # Get request body
        req_body = req.get_json()
        if not req_body:
            return func.HttpResponse(
                json.dumps({
                    "error": "Request body is required",
                    "help": "Send JSON sensor data in request body",
                    "timestamp": datetime.utcnow().isoformat()
                }),
                status_code=400,
                mimetype="application/json"
            )
        
        # Validate sensor data
        try:
            validated_data = validate_sensor_data(req_body)
        except ValueError as e:
            return func.HttpResponse(
                json.dumps({
                    "error": f"Validation failed: {str(e)}",
                    "timestamp": datetime.utcnow().isoformat()
                }),
                status_code=400,
                mimetype="application/json"
            )
        
        # Check ArcGIS credentials
        username = os.environ.get('ARCGIS_USERNAME', '')
        password = os.environ.get('ARCGIS_PASSWORD', '')
        
        if not username or not password:
            return func.HttpResponse(
                json.dumps({
                    "error": "ArcGIS credentials not configured",
                    "help": "Configure ARCGIS_USERNAME and ARCGIS_PASSWORD environment variables",
                    "timestamp": datetime.utcnow().isoformat()
                }),
                status_code=500,
                mimetype="application/json"
            )
        
        # Get feature service and add the historical record
        feature_service = get_feature_service()
        
        # Add processing timestamp to track when record was received
        processing_timestamp = datetime.utcnow().isoformat()
        
        # Add the feature (always creates new record - no updates)
        result = feature_service.add_features([validated_data])
        
        if result['success'] and result['added_count'] > 0:
            # Extract OBJECTID from successful result
            arcgis_objectid = None
            if result['results'] and len(result['results']) > 0:
                first_result = result['results'][0]
                if first_result.get('success'):
                    arcgis_objectid = first_result.get('objectId')
            
            response_data = {
                "status": "success",
                "message": "Historical sensor data record created successfully",
                "asset_id": validated_data.get('asset_id'),
                "operation": "add",
                "alarm_date": validated_data.get('alarm_date'),
                "processed_timestamp": processing_timestamp,
                "arcgis_objectid": arcgis_objectid,
                "added_count": result['added_count'],
                "failed_count": result['failed_count']
            }
            
            logging.info(f"Sensor data added successfully: asset_id={validated_data.get('asset_id')}, objectid={arcgis_objectid}")
            
            return func.HttpResponse(
                json.dumps(response_data),
                status_code=200,
                mimetype="application/json"
            )
        else:
            # Handle case where add operation failed
            error_details = []
            if result.get('results'):
                for res in result['results']:
                    if not res.get('success') and res.get('error'):
                        error_details.append(res['error'])
            
            error_msg = f"Failed to add sensor data: {'; '.join(error_details)}" if error_details else "Unknown error during add operation"
            
            return func.HttpResponse(
                json.dumps({
                    "error": error_msg,
                    "asset_id": validated_data.get('asset_id'),
                    "timestamp": processing_timestamp
                }),
                status_code=500,
                mimetype="application/json"
            )
    
    except Exception as e:
        logging.error(f"Sensor data processing failed: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "error": f"Internal server error: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="features/{asset_id}", auth_level=func.AuthLevel.ANONYMOUS)
def get_feature_by_asset_id(req: func.HttpRequest) -> func.HttpResponse:
    """Get latest sensor reading for specific asset ID"""
    logging.info('Get feature by asset ID requested')
    
    try:
        asset_id = req.route_params.get('asset_id')
        if not asset_id:
            return func.HttpResponse(
                json.dumps({
                    "error": "Asset ID is required in URL path",
                    "timestamp": datetime.utcnow().isoformat()
                }),
                status_code=400,
                mimetype="application/json"
            )
        
        # Check ArcGIS credentials
        username = os.environ.get('ARCGIS_USERNAME', '')
        password = os.environ.get('ARCGIS_PASSWORD', '')
        
        if not username or not password:
            return func.HttpResponse(
                json.dumps({
                    "error": "ArcGIS credentials not configured",
                    "timestamp": datetime.utcnow().isoformat()
                }),
                status_code=500,
                mimetype="application/json"
            )
        
        # Get feature service and query for the asset
        feature_service = get_feature_service()
        
        # Query for this specific asset, ordered by alarm_date descending to get latest
        result = feature_service.query_features(
            where_clause=f"asset_id = '{asset_id}'",
            return_fields="*",
            max_records=1,
            order_by="alarm_date DESC"
        )
        
        if result['success']:
            if result['count'] > 0:
                latest_record = result['features'][0]
                
                response_data = {
                    "found": True,
                    "asset_id": asset_id,
                    "latest_record": latest_record,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                return func.HttpResponse(
                    json.dumps(response_data),
                    status_code=200,
                    mimetype="application/json"
                )
            else:
                return func.HttpResponse(
                    json.dumps({
                        "found": False,
                        "asset_id": asset_id,
                        "message": "No records found for this asset ID",
                        "timestamp": datetime.utcnow().isoformat()
                    }),
                    status_code=404,
                    mimetype="application/json"
                )
        else:
            return func.HttpResponse(
                json.dumps({
                    "error": "Feature query failed",
                    "asset_id": asset_id,
                    "timestamp": datetime.utcnow().isoformat()
                }),
                status_code=500,
                mimetype="application/json"
            )
    
    except Exception as e:
        logging.error(f"Feature query failed: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "error": f"Internal server error: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }),
            status_code=500,
            mimetype="application/json"
        )