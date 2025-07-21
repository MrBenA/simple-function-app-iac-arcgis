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
                'expiration': 60  # 60 minutes
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

# Global REST client instance
_rest_client = None

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