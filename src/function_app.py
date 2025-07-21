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
URLLIB_AVAILABLE = True

app = func.FunctionApp()

@app.route(route="health", auth_level=func.AuthLevel.ANONYMOUS)
def health(req: func.HttpRequest) -> func.HttpResponse:
    """Simple health check endpoint"""
    logging.info('Health check requested')
    
    health_data = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0-python-3.11-urllib",
        "python_version": "3.11",
        "requests_available": REQUESTS_AVAILABLE,
        "urllib_available": URLLIB_AVAILABLE
    }
    
    return func.HttpResponse(
        json.dumps(health_data),
        status_code=200,
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