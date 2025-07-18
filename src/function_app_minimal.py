import azure.functions as func
import logging
import json
from datetime import datetime

app = func.FunctionApp()

@app.route(route="minimal", auth_level=func.AuthLevel.ANONYMOUS)
def minimal(req: func.HttpRequest) -> func.HttpResponse:
    """Minimal test endpoint"""
    logging.info('Minimal endpoint requested')
    
    return func.HttpResponse(
        json.dumps({
            "status": "working",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Minimal function is working"
        }),
        status_code=200,
        mimetype="application/json"
    )

@app.route(route="test", auth_level=func.AuthLevel.ANONYMOUS)
def test(req: func.HttpRequest) -> func.HttpResponse:
    """Test endpoint"""
    logging.info('Test endpoint requested')
    
    return func.HttpResponse(
        "Hello from Azure Functions! This is a minimal test.",
        status_code=200
    )