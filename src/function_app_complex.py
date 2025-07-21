import azure.functions as func
import logging
import json
import os
import requests
from datetime import datetime, timedelta

class ArcGISRestClient:
    """Lightweight ArcGIS REST API client"""
    def __init__(self, org_url, username, password):
        self.org_url = org_url.rstrip('/')
        self.username = username
        self.password = password
        self.token = None
        self.token_expires = None
    
    def get_token(self, force_refresh=False):
        """Get or refresh authentication token"""
        if not force_refresh and self.token and self.token_expires > datetime.now():
            return self.token
        
        try:
            token_url = f"{self.org_url}/sharing/rest/generateToken"
            data = {
                'username': self.username,
                'password': self.password,
                'client': 'requestip',
                'f': 'json',
                'expiration': 60  # 60 minutes
            }
            
            response = requests.post(token_url, data=data, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if 'error' in result:
                raise Exception(f"Authentication failed: {result['error']}")
            
            self.token = result['token']
            self.token_expires = datetime.now() + timedelta(minutes=55)  # 5min buffer
            
            logging.info(f"Successfully obtained ArcGIS token, expires: {self.token_expires}")
            return self.token
            
        except Exception as e:
            logging.error(f"Failed to get ArcGIS token: {str(e)}")
            raise
    
    def test_connection(self):
        """Test ArcGIS Online connectivity"""
        try:
            token = self.get_token()
            
            # Test with a simple portal info request
            portal_url = f"{self.org_url}/sharing/rest/portals/self"
            data = {'token': token, 'f': 'json'}
            
            response = requests.get(portal_url, params=data, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if 'error' in result:
                raise Exception(f"Portal info failed: {result['error']}")
            
            return {
                'success': True,
                'org_name': result.get('name', 'Unknown'),
                'user': result.get('user', {}).get('username', 'Unknown')
            }
            
        except Exception as e:
            logging.error(f"ArcGIS connection test failed: {str(e)}")
            return {'success': False, 'error': str(e)}

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
    """Health check with ArcGIS REST API connectivity test"""
    logging.info('Health check requested')
    
    health_data = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0-rest-api",
        "dependencies": {
            "requests": "available",
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
        "Hello from Azure Functions! This is the ArcGIS function app (minimal version).",
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
        response_text = f"Hello, {name}! Welcome to the ArcGIS function app."
    else:
        response_text = "Hello, World! Welcome to the ArcGIS function app. Pass a 'name' parameter to personalize this message."
    
    return func.HttpResponse(
        response_text,
        status_code=200
    )

@app.route(route="arcgis-test", auth_level=func.AuthLevel.ANONYMOUS)
def arcgis_test(req: func.HttpRequest) -> func.HttpResponse:
    """Test ArcGIS REST API connectivity"""
    logging.info('ArcGIS REST API test requested')
    
    try:
        username = os.environ.get('ARCGIS_USERNAME', '')
        password = os.environ.get('ARCGIS_PASSWORD', '')
        
        if not username or not password:
            return func.HttpResponse(
                json.dumps({
                    "error": "ArcGIS credentials not configured",
                    "help": "Set ARCGIS_USERNAME and ARCGIS_PASSWORD environment variables"
                }),
                status_code=400,
                mimetype="application/json"
            )
        
        rest_client = get_rest_client()
        connection_test = rest_client.test_connection()
        
        if connection_test['success']:
            response_data = {
                "status": "success",
                "message": "ArcGIS REST API connection successful",
                "org_name": connection_test['org_name'],
                "user": connection_test['user'],
                "token_expires": rest_client.token_expires.isoformat() if rest_client.token_expires else None,
                "approach": "REST API (no Python API dependency)",
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