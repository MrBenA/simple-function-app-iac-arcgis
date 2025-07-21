import azure.functions as func
import logging
import json
import os
import requests
from datetime import datetime

# Test simple requests import
try:
    import requests
    REQUESTS_AVAILABLE = True
    logging.info("Requests library imported successfully")
except ImportError as e:
    REQUESTS_AVAILABLE = False
    logging.error(f"Requests import failed: {e}")

app = func.FunctionApp()

@app.route(route="health", auth_level=func.AuthLevel.ANONYMOUS)
def health(req: func.HttpRequest) -> func.HttpResponse:
    """Simple health check endpoint"""
    logging.info('Health check requested')
    
    health_data = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0-rest-api-test",
        "requests_available": REQUESTS_AVAILABLE
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
        "Hello from Azure Functions! REST API test version.",
        status_code=200
    )

@app.route(route="requests-test", auth_level=func.AuthLevel.ANONYMOUS)
def requests_test(req: func.HttpRequest) -> func.HttpResponse:
    """Test requests library"""
    logging.info('Requests test requested')
    
    if not REQUESTS_AVAILABLE:
        return func.HttpResponse(
            json.dumps({"error": "Requests library not available"}),
            status_code=500,
            mimetype="application/json"
        )
    
    try:
        # Simple HTTP test
        response = requests.get('https://httpbin.org/get', timeout=5)
        
        return func.HttpResponse(
            json.dumps({
                "status": "success",
                "message": "Requests library working",
                "test_url": "https://httpbin.org/get",
                "response_status": response.status_code,
                "timestamp": datetime.utcnow().isoformat()
            }),
            status_code=200,
            mimetype="application/json"
        )
    
    except Exception as e:
        logging.error(f"Requests test failed: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }),
            status_code=500,
            mimetype="application/json"
        )