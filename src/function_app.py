import azure.functions as func
import logging
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any

# Try to import optional dependencies
try:
    from pydantic import BaseModel, ValidationError, Field
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    logging.warning("Pydantic not available, sensor data validation will be limited")

try:
    from arcgis.gis import GIS
    from arcgis.features import FeatureLayer
    from config import ArcGISConfig
    ARCGIS_AVAILABLE = True
except ImportError as e:
    ARCGIS_AVAILABLE = False
    logging.warning(f"ArcGIS not available: {e}")

app = func.FunctionApp()

# Pydantic model for sensor data validation
class SensorData(BaseModel):
    location: str = Field(..., description="Sensor location")
    node_id: str = Field(..., description="Node identifier")
    block: str = Field(..., description="Block identifier")
    level: int = Field(..., description="Level number")
    ward: str = Field(..., description="Ward identifier")
    asset_type: str = Field(..., description="Type of asset")
    asset_id: str = Field(..., description="Asset identifier")
    alarm_code: int = Field(..., description="Alarm code")
    object_name: str = Field(..., description="Object name")
    description: str = Field(..., description="Description")
    present_value: float = Field(..., description="Present value")
    threshold_value: float = Field(..., description="Threshold value")
    min_value: float = Field(..., description="Minimum value")
    max_value: float = Field(..., description="Maximum value")
    resolution: float = Field(..., description="Resolution")
    units: str = Field(..., description="Units of measurement")
    alarm_status: str = Field(..., description="Alarm status")
    event_state: str = Field(..., description="Event state")
    alarm_date: str = Field(..., description="Alarm date in ISO format")
    device_type: str = Field(..., description="Type of device")

# Global variables for connection management
_gis_connection = None
_feature_layer = None
_config = None

def get_gis_connection():
    """Get or create ArcGIS Online connection"""
    global _gis_connection, _config
    
    if _gis_connection is None:
        try:
            _config = ArcGISConfig()
            logging.info(f"Connecting to ArcGIS Online: {_config.arcgis_url}")
            
            _gis_connection = GIS(
                url=_config.arcgis_url,
                username=_config.arcgis_username,
                password=_config.arcgis_password
            )
            
            logging.info(f"Successfully connected to ArcGIS Online as: {_gis_connection.users.me.username}")
            
        except Exception as e:
            logging.error(f"Failed to connect to ArcGIS Online: {str(e)}")
            raise
    
    return _gis_connection

def get_feature_layer():
    """Get or create feature layer connection"""
    global _feature_layer, _config
    
    if _feature_layer is None:
        try:
            gis = get_gis_connection()
            
            # Get the feature service item
            feature_service = gis.content.get(_config.feature_service_id)
            if not feature_service:
                raise ValueError(f"Feature service not found: {_config.feature_service_id}")
            
            # Get the feature layer
            _feature_layer = feature_service.layers[_config.feature_layer_index]
            
            logging.info(f"Successfully connected to feature layer: {_feature_layer.properties.name}")
            
        except Exception as e:
            logging.error(f"Failed to connect to feature layer: {str(e)}")
            raise
    
    return _feature_layer

def validate_sensor_data(data: dict) -> SensorData:
    """Validate sensor data using Pydantic model"""
    try:
        return SensorData(**data)
    except ValidationError as e:
        logging.error(f"Sensor data validation failed: {e}")
        raise ValueError(f"Invalid sensor data: {e}")

def prepare_feature_attributes(sensor_data: SensorData) -> Dict[str, Any]:
    """Prepare feature attributes for ArcGIS feature service"""
    # Convert Pydantic model to dict
    data_dict = sensor_data.dict()
    
    # Map sensor fields to ArcGIS fields using configuration
    config = ArcGISConfig()
    mapped_data = config.map_sensor_data(data_dict)
    
    # Add timestamp for record creation
    mapped_data['record_created'] = datetime.utcnow().isoformat()
    
    # Convert alarm_date to proper format if needed
    if 'alarm_date' in mapped_data:
        try:
            # Parse and reformat date to ensure consistency
            parsed_date = datetime.fromisoformat(mapped_data['alarm_date'].replace('Z', '+00:00'))
            mapped_data['alarm_date'] = parsed_date.isoformat()
        except ValueError:
            logging.warning(f"Invalid date format in alarm_date: {mapped_data['alarm_date']}")
    
    return mapped_data

def add_or_update_feature(sensor_data: SensorData) -> Dict[str, Any]:
    """Add or update feature in ArcGIS feature service"""
    try:
        feature_layer = get_feature_layer()
        
        # Prepare feature attributes
        attributes = prepare_feature_attributes(sensor_data)
        
        # Check if feature already exists based on asset_id
        existing_features = feature_layer.query(
            where=f"asset_id = '{sensor_data.asset_id}'",
            return_geometry=False
        )
        
        if existing_features.features:
            # Update existing feature
            logging.info(f"Updating existing feature for asset_id: {sensor_data.asset_id}")
            
            # Get the OBJECTID of the existing feature
            objectid = existing_features.features[0].attributes['OBJECTID']
            attributes['OBJECTID'] = objectid
            
            # Update the feature
            update_features = [{
                "attributes": attributes
            }]
            
            result = feature_layer.edit_features(updates=update_features)
            
            operation_type = "update"
            
        else:
            # Add new feature
            logging.info(f"Adding new feature for asset_id: {sensor_data.asset_id}")
            
            # Create new feature
            new_features = [{
                "attributes": attributes
            }]
            
            result = feature_layer.edit_features(adds=new_features)
            
            operation_type = "add"
        
        # Check if operation was successful
        if operation_type == "add":
            success = result.get('addResults', [{}])[0].get('success', False)
            error_msg = result.get('addResults', [{}])[0].get('error', {}).get('description', '')
        else:
            success = result.get('updateResults', [{}])[0].get('success', False)
            error_msg = result.get('updateResults', [{}])[0].get('error', {}).get('description', '')
        
        if not success:
            raise Exception(f"ArcGIS operation failed: {error_msg}")
        
        return {
            "success": True,
            "operation": operation_type,
            "asset_id": sensor_data.asset_id,
            "message": f"Feature {operation_type}d successfully",
            "result": result
        }
        
    except Exception as e:
        logging.error(f"Error adding/updating feature: {str(e)}")
        raise

@app.route(route="health", auth_level=func.AuthLevel.ANONYMOUS)
def health(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint with ArcGIS connection validation"""
    logging.info('Health check requested')
    
    health_data = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0-arcgis",
        "dependencies": {
            "arcgis_online": "unknown",
            "feature_service": "unknown"
        }
    }
    
    # Test ArcGIS Online connection
    try:
        gis = get_gis_connection()
        health_data["dependencies"]["arcgis_online"] = "healthy"
        health_data["arcgis_user"] = gis.users.me.username
        health_data["arcgis_org"] = gis.properties.name
        
        # Test feature service connection
        feature_layer = get_feature_layer()
        health_data["dependencies"]["feature_service"] = "healthy"
        health_data["feature_layer"] = feature_layer.properties.name
        
    except Exception as e:
        health_data["dependencies"]["arcgis_online"] = f"unhealthy: {str(e)}"
        health_data["status"] = "degraded"
    
    return func.HttpResponse(
        json.dumps(health_data),
        status_code=200,
        mimetype="application/json"
    )

@app.route(route="sensor-data", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
def ingest_sensor_data(req: func.HttpRequest) -> func.HttpResponse:
    """Ingest sensor data and write to ArcGIS feature service"""
    logging.info('Sensor data ingestion requested')
    
    try:
        # Parse request body
        req_body = req.get_json()
        if not req_body:
            return func.HttpResponse(
                json.dumps({"error": "Request body is required"}),
                status_code=400,
                mimetype="application/json"
            )
        
        logging.info(f"Received sensor data: {json.dumps(req_body, indent=2)}")
        
        # Validate sensor data
        sensor_data = validate_sensor_data(req_body)
        
        # Add or update feature in ArcGIS
        result = add_or_update_feature(sensor_data)
        
        response = {
            "status": "success",
            "message": "Sensor data processed successfully",
            "asset_id": sensor_data.asset_id,
            "operation": result["operation"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logging.info(f"Sensor data processed successfully: {response}")
        
        return func.HttpResponse(
            json.dumps(response),
            status_code=201,
            mimetype="application/json"
        )
        
    except ValueError as e:
        logging.error(f"Validation error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=400,
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Error processing sensor data: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "error": "Internal server error",
                "details": str(e)
            }),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="features/{asset_id}", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
def get_feature_by_asset_id(req: func.HttpRequest) -> func.HttpResponse:
    """Get feature data by asset ID"""
    logging.info('Feature query by asset ID requested')
    
    try:
        asset_id = req.route_params.get('asset_id')
        if not asset_id:
            return func.HttpResponse(
                json.dumps({"error": "Asset ID is required"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Query feature layer
        feature_layer = get_feature_layer()
        
        features = feature_layer.query(
            where=f"asset_id = '{asset_id}'",
            return_geometry=False,
            out_fields="*"
        )
        
        if not features.features:
            return func.HttpResponse(
                json.dumps({"error": f"No feature found for asset_id: {asset_id}"}),
                status_code=404,
                mimetype="application/json"
            )
        
        # Convert features to JSON-serializable format
        feature_data = []
        for feature in features.features:
            feature_data.append({
                "attributes": feature.attributes,
                "geometry": feature.geometry
            })
        
        response = {
            "asset_id": asset_id,
            "count": len(feature_data),
            "features": feature_data
        }
        
        return func.HttpResponse(
            json.dumps(response),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f"Error querying feature: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="features", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
def list_features(req: func.HttpRequest) -> func.HttpResponse:
    """List all features with optional filtering"""
    logging.info('Feature list requested')
    
    try:
        # Get query parameters
        limit = int(req.params.get('limit', 10))
        where_clause = req.params.get('where', '1=1')
        
        # Query feature layer
        feature_layer = get_feature_layer()
        
        features = feature_layer.query(
            where=where_clause,
            return_geometry=False,
            out_fields="*",
            result_record_count=limit
        )
        
        # Convert features to JSON-serializable format
        feature_data = []
        for feature in features.features:
            feature_data.append(feature.attributes)
        
        response = {
            "count": len(feature_data),
            "limit": limit,
            "where": where_clause,
            "features": feature_data
        }
        
        return func.HttpResponse(
            json.dumps(response),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f"Error listing features: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json"
        )

# Legacy compatibility endpoints
@app.route(route="test", auth_level=func.AuthLevel.ANONYMOUS)
def test(req: func.HttpRequest) -> func.HttpResponse:
    """Legacy test endpoint for compatibility"""
    logging.info('Test endpoint requested')
    
    return func.HttpResponse(
        "Hello from Azure Functions! This is the ArcGIS-enabled function app for sensor data processing.",
        status_code=200
    )

@app.route(route="hello", auth_level=func.AuthLevel.ANONYMOUS)
def hello(req: func.HttpRequest) -> func.HttpResponse:
    """Legacy hello endpoint for compatibility"""
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
        response_text = f"Hello, {name}! Welcome to the ArcGIS sensor data processing platform."
    else:
        response_text = "Hello, World! Welcome to the ArcGIS sensor data processing platform."
    
    return func.HttpResponse(
        response_text,
        status_code=200
    )

@app.route(route="status", auth_level=func.AuthLevel.ANONYMOUS)
def status(req: func.HttpRequest) -> func.HttpResponse:
    """Simple status endpoint to test function registration"""
    logging.info('Status endpoint requested')
    
    status_data = {
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "python_version": sys.version,
        "arcgis_available": ARCGIS_AVAILABLE,
        "pydantic_available": PYDANTIC_AVAILABLE
    }
    
    return func.HttpResponse(
        json.dumps(status_data),
        status_code=200,
        mimetype="application/json"
    )