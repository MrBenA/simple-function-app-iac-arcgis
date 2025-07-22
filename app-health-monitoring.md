# Health Monitoring Feature

## Overview

The health monitoring feature provides comprehensive system validation and monitoring endpoints for the Azure Function App and its dependencies. This feature includes ArcGIS connectivity validation, system status reporting, and detailed health metrics to ensure reliable operation and effective troubleshooting.

## API Endpoints

### GET /api/health

**Purpose**: Comprehensive health check with dependency validation

**HTTP Method**: GET  
**Authentication**: Anonymous (accessible for monitoring systems)  
**Response Format**: JSON

**Example Request**:
```bash
curl https://your-function-app.azurewebsites.net/api/health
```

**Healthy Response (200 OK)**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "python_version": "3.11.0",
  "function_runtime": "~4",
  "dependencies": {
    "arcgis_online": {
      "status": "healthy",
      "response_time_ms": 245,
      "last_token_refresh": "2024-01-15T09:30:00.000Z",
      "token_expires_in_minutes": 55
    },
    "feature_service": {
      "status": "healthy",
      "service_id": "f4682a40e60847fe8289408e73933b82",
      "response_time_ms": 180,
      "total_features": 1247
    }
  },
  "arcgis_connection": {
    "user": "your-username",
    "organization": "Your Organization",
    "service_url": "https://services-eu1.arcgis.com/veDTgAL7B9EBogdG/arcgis/rest/services/SensorDataService/FeatureServer",
    "layer_name": "SensorReadings"
  },
  "system_info": {
    "deployment_region": "West Europe",
    "consumption_plan": true,
    "memory_usage_mb": 78,
    "environment_variables_configured": 5
  }
}
```

**Unhealthy Response (503 Service Unavailable)**:
```json
{
  "status": "unhealthy", 
  "timestamp": "2024-01-15T10:30:00.000Z",
  "version": "1.0.0",
  "error": "ArcGIS connection failed",
  "dependencies": {
    "arcgis_online": {
      "status": "unhealthy",
      "error": "Authentication failed: Invalid username or password",
      "last_attempt": "2024-01-15T10:29:45.000Z"
    },
    "feature_service": {
      "status": "unknown",
      "error": "Cannot test - ArcGIS connection failed"
    }
  },
  "troubleshooting": {
    "check_credentials": "Verify ARCGIS_USERNAME and ARCGIS_PASSWORD in Function App settings",
    "check_network": "Ensure Function App can reach www.arcgis.com",
    "check_permissions": "Verify user has access to specified feature service"
  }
}
```

### Additional Health Endpoints

#### GET /api/health/simple

**Purpose**: Lightweight health check for load balancers

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

#### GET /api/health/dependencies

**Purpose**: Detailed dependency status only

```json
{
  "arcgis_online": "healthy",
  "feature_service": "healthy",
  "last_check": "2024-01-15T10:30:00.000Z"
}
```

## Health Check Implementation

### Core Health Check Logic

```python
import json
import logging
import os
import time
from datetime import datetime, timezone
import azure.functions as func

@app.route(route="health", auth_level=func.AuthLevel.ANONYMOUS)
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Comprehensive health check with dependency validation"""
    
    health_data = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "python_version": sys.version.split()[0],
        "function_runtime": "~4",
        "dependencies": {},
        "system_info": {}
    }
    
    overall_healthy = True
    errors = []
    
    # Check ArcGIS Online connectivity
    try:
        arcgis_health = check_arcgis_health()
        health_data["dependencies"]["arcgis_online"] = arcgis_health
        
        if arcgis_health["status"] != "healthy":
            overall_healthy = False
            errors.append("ArcGIS Online connection failed")
            
    except Exception as e:
        health_data["dependencies"]["arcgis_online"] = {
            "status": "unhealthy",
            "error": str(e),
            "last_attempt": datetime.now(timezone.utc).isoformat()
        }
        overall_healthy = False
        errors.append(f"ArcGIS health check failed: {str(e)}")
    
    # Check Feature Service accessibility
    try:
        if health_data["dependencies"]["arcgis_online"]["status"] == "healthy":
            feature_service_health = check_feature_service_health()
            health_data["dependencies"]["feature_service"] = feature_service_health
            
            if feature_service_health["status"] != "healthy":
                overall_healthy = False
                errors.append("Feature Service access failed")
        else:
            health_data["dependencies"]["feature_service"] = {
                "status": "unknown",
                "error": "Cannot test - ArcGIS connection failed"
            }
    except Exception as e:
        health_data["dependencies"]["feature_service"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_healthy = False
        errors.append(f"Feature Service health check failed: {str(e)}")
    
    # Add system information
    health_data["system_info"] = get_system_info()
    
    # Set overall status
    if not overall_healthy:
        health_data["status"] = "unhealthy"
        health_data["errors"] = errors
        health_data["troubleshooting"] = get_troubleshooting_info()
        status_code = 503
    else:
        status_code = 200
    
    return func.HttpResponse(
        json.dumps(health_data, indent=2),
        status_code=status_code,
        mimetype="application/json"
    )
```

### ArcGIS Health Check

```python
def check_arcgis_health():
    """Validate ArcGIS Online connectivity and authentication"""
    start_time = time.time()
    
    try:
        rest_client = get_rest_client()
        
        # Test token generation
        token = rest_client.get_token()
        
        # Test portal connectivity
        portal_info = rest_client.validate_connection()
        
        response_time = int((time.time() - start_time) * 1000)
        
        # Calculate token expiration
        if rest_client.token_expires:
            expires_in = int((rest_client.token_expires - datetime.now()).total_seconds() / 60)
        else:
            expires_in = None
        
        return {
            "status": "healthy",
            "response_time_ms": response_time,
            "user": portal_info.get("user"),
            "organization": portal_info.get("org"),
            "last_token_refresh": rest_client.token_expires.isoformat() if rest_client.token_expires else None,
            "token_expires_in_minutes": expires_in
        }
        
    except Exception as e:
        response_time = int((time.time() - start_time) * 1000)
        return {
            "status": "unhealthy",
            "response_time_ms": response_time,
            "error": str(e),
            "last_attempt": datetime.now(timezone.utc).isoformat()
        }
```

### Feature Service Health Check

```python
def check_feature_service_health():
    """Validate feature service accessibility and basic operations"""
    start_time = time.time()
    
    try:
        feature_service = get_feature_service()
        
        # Test basic query operation
        result = feature_service.query_features(
            where_clause="1=1",
            return_fields="OBJECTID",
            max_records=1
        )
        
        # Get total feature count
        count_result = feature_service.query_features(
            where_clause="1=1",
            return_fields="OBJECTID",
            max_records=1000  # Get up to 1000 to estimate total
        )
        
        response_time = int((time.time() - start_time) * 1000)
        
        return {
            "status": "healthy",
            "service_id": os.environ.get('FEATURE_SERVICE_ID'),
            "layer_index": int(os.environ.get('FEATURE_LAYER_INDEX', '0')),
            "response_time_ms": response_time,
            "total_features": count_result['count'],
            "service_accessible": True
        }
        
    except Exception as e:
        response_time = int((time.time() - start_time) * 1000)
        return {
            "status": "unhealthy",
            "response_time_ms": response_time,
            "error": str(e),
            "service_accessible": False
        }
```

### System Information Collection

```python
def get_system_info():
    """Collect system and environment information"""
    import platform
    
    try:
        # Memory usage estimation
        memory_usage_mb = None
        try:
            import psutil
            memory_info = psutil.Process().memory_info()
            memory_usage_mb = int(memory_info.rss / 1024 / 1024)
        except ImportError:
            # psutil not available in Azure Functions by default
            pass
        
        # Environment variable validation
        required_env_vars = [
            'ARCGIS_URL', 'ARCGIS_USERNAME', 'ARCGIS_PASSWORD', 
            'FEATURE_SERVICE_ID', 'FEATURE_LAYER_INDEX'
        ]
        
        configured_vars = sum(1 for var in required_env_vars if os.environ.get(var))
        
        return {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "deployment_region": os.environ.get('REGION', 'Unknown'),
            "consumption_plan": os.environ.get('FUNCTIONS_WORKER_RUNTIME') == 'python',
            "memory_usage_mb": memory_usage_mb,
            "environment_variables_configured": configured_vars,
            "total_required_variables": len(required_env_vars)
        }
        
    except Exception as e:
        return {
            "error": f"Could not collect system info: {str(e)}",
            "environment_variables_configured": len([var for var in required_env_vars if os.environ.get(var)])
        }
```

## Monitoring Integration

### Application Insights Integration

```python
import logging
from opencensus.ext.azure.log_exporter import AzureLogHandler

# Configure Application Insights logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add Application Insights handler if connection string is available
if os.environ.get('APPLICATIONINSIGHTS_CONNECTION_STRING'):
    logger.addHandler(AzureLogHandler())

def log_health_metrics(health_data):
    """Log health metrics to Application Insights"""
    
    # Log overall health status
    logger.info("Health Check", extra={
        'custom_dimensions': {
            'status': health_data['status'],
            'arcgis_status': health_data['dependencies']['arcgis_online']['status'],
            'feature_service_status': health_data['dependencies']['feature_service']['status'],
            'response_time_arcgis': health_data['dependencies']['arcgis_online'].get('response_time_ms'),
            'response_time_feature_service': health_data['dependencies']['feature_service'].get('response_time_ms'),
            'total_features': health_data['dependencies']['feature_service'].get('total_features')
        }
    })
    
    # Log errors separately for alerting
    if health_data['status'] == 'unhealthy':
        logger.error(f"Health Check Failed: {'; '.join(health_data.get('errors', []))}")
```

### Prometheus Metrics (Future Enhancement)

```python
# Future implementation for Prometheus metrics
def export_prometheus_metrics():
    """Export health metrics in Prometheus format"""
    metrics = []
    
    # System health gauge
    metrics.append(f"azure_function_health{{status=\"healthy\"}} 1")
    
    # Dependency health
    metrics.append(f"arcgis_connection_status{{status=\"healthy\"}} 1")
    metrics.append(f"feature_service_status{{status=\"healthy\"}} 1")
    
    # Response times
    metrics.append(f"arcgis_response_time_ms 245")
    metrics.append(f"feature_service_response_time_ms 180")
    
    # Feature counts
    metrics.append(f"total_sensor_features 1247")
    
    return "\n".join(metrics)
```

## Error Detection & Troubleshooting

### Common Issue Detection

```python
def get_troubleshooting_info():
    """Provide troubleshooting guidance based on error patterns"""
    troubleshooting = {}
    
    # Check environment variables
    missing_vars = []
    required_vars = ['ARCGIS_USERNAME', 'ARCGIS_PASSWORD', 'FEATURE_SERVICE_ID']
    
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        troubleshooting['missing_environment_variables'] = {
            'issue': f"Missing required variables: {', '.join(missing_vars)}",
            'solution': "Configure missing variables in Function App Settings"
        }
    
    # Check credential format
    username = os.environ.get('ARCGIS_USERNAME', '')
    if '@' not in username and username:
        troubleshooting['username_format'] = {
            'issue': "ArcGIS username might need organization suffix",
            'solution': "Try format: username@organization or username.organization"
        }
    
    # Check service ID format
    service_id = os.environ.get('FEATURE_SERVICE_ID', '')
    if service_id and len(service_id) != 32:
        troubleshooting['service_id_format'] = {
            'issue': "Feature Service ID format appears invalid",
            'solution': "Service ID should be 32-character hexadecimal string"
        }
    
    return troubleshooting
```

### Error Pattern Analysis

```python
def analyze_error_pattern(error_message):
    """Analyze error patterns to provide specific guidance"""
    error_lower = error_message.lower()
    
    if 'invalid username or password' in error_lower:
        return {
            'category': 'authentication',
            'guidance': 'Verify ArcGIS Online credentials in Function App settings',
            'check_list': [
                'Confirm username is correct',
                'Verify password has not expired',
                'Check if account requires 2FA (not supported)',
                'Ensure account has necessary permissions'
            ]
        }
    
    elif 'timeout' in error_lower:
        return {
            'category': 'connectivity',
            'guidance': 'Network connectivity issue with ArcGIS Online',
            'check_list': [
                'Check Azure Function outbound connectivity',
                'Verify ArcGIS Online service status',
                'Consider increasing timeout values'
            ]
        }
    
    elif 'feature service' in error_lower:
        return {
            'category': 'service_access',
            'guidance': 'Feature service access problem',
            'check_list': [
                'Verify Feature Service ID is correct',
                'Check if service exists and is shared',
                'Confirm user has edit permissions',
                'Validate layer index (usually 0)'
            ]
        }
    
    else:
        return {
            'category': 'unknown',
            'guidance': 'Unexpected error - check logs for details',
            'check_list': [
                'Review full error message in logs',
                'Check Application Insights for patterns',
                'Verify all configuration settings'
            ]
        }
```

## Alerting & Notifications

### Health Status Thresholds

```python
class HealthThresholds:
    """Define thresholds for health status determination"""
    
    # Response time thresholds (milliseconds)
    RESPONSE_TIME_WARNING = 1000    # 1 second
    RESPONSE_TIME_CRITICAL = 5000   # 5 seconds
    
    # Token expiration warning (minutes)
    TOKEN_EXPIRATION_WARNING = 10   # 10 minutes before expiration
    
    # Feature count thresholds
    FEATURE_COUNT_MIN = 1           # At least 1 feature should exist
    FEATURE_COUNT_MAX = 100000      # Alert if unusually high

def evaluate_health_status(health_data):
    """Evaluate health status against defined thresholds"""
    warnings = []
    critical = []
    
    # Check response times
    arcgis_response = health_data['dependencies']['arcgis_online'].get('response_time_ms', 0)
    if arcgis_response > HealthThresholds.RESPONSE_TIME_CRITICAL:
        critical.append(f"ArcGIS response time critical: {arcgis_response}ms")
    elif arcgis_response > HealthThresholds.RESPONSE_TIME_WARNING:
        warnings.append(f"ArcGIS response time warning: {arcgis_response}ms")
    
    # Check token expiration
    token_expires_in = health_data['dependencies']['arcgis_online'].get('token_expires_in_minutes', 0)
    if token_expires_in <= HealthThresholds.TOKEN_EXPIRATION_WARNING:
        warnings.append(f"ArcGIS token expires soon: {token_expires_in} minutes")
    
    # Check feature count
    feature_count = health_data['dependencies']['feature_service'].get('total_features', 0)
    if feature_count < HealthThresholds.FEATURE_COUNT_MIN:
        warnings.append(f"Low feature count: {feature_count}")
    elif feature_count > HealthThresholds.FEATURE_COUNT_MAX:
        warnings.append(f"High feature count: {feature_count}")
    
    return {
        'warnings': warnings,
        'critical': critical,
        'overall_status': 'critical' if critical else ('warning' if warnings else 'healthy')
    }
```

## Testing & Validation

### Health Check Testing

```bash
# Basic health check
curl -i https://your-function-app.azurewebsites.net/api/health

# Simple health check for load balancers
curl -i https://your-function-app.azurewebsites.net/api/health/simple

# Dependencies only
curl https://your-function-app.azurewebsites.net/api/health/dependencies | jq '.'
```

### Automated Health Monitoring

```bash
#!/bin/bash
# health-monitor.sh - Simple monitoring script

FUNCTION_URL="https://your-function-app.azurewebsites.net"
HEALTH_ENDPOINT="$FUNCTION_URL/api/health"

response=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_ENDPOINT)

if [ "$response" -eq 200 ]; then
    echo "$(date): Health check PASSED"
    exit 0
else
    echo "$(date): Health check FAILED (HTTP $response)"
    curl -s $HEALTH_ENDPOINT | jq '.errors[]' 2>/dev/null || echo "No error details available"
    exit 1
fi
```

## Performance Metrics

### Key Health Metrics

| Metric | Healthy Range | Warning Threshold | Critical Threshold |
|--------|---------------|-------------------|-------------------|
| ArcGIS Response Time | < 500ms | 500ms - 2s | > 2s |
| Feature Service Response | < 300ms | 300ms - 1s | > 1s |
| Token Expiration | > 30 min | 10-30 min | < 10 min |
| Memory Usage | < 100MB | 100-200MB | > 200MB |
| Feature Count Growth | Normal | Rapid increase | Excessive count |

## Advanced Health Features

### Dependency Health Matrix

```python
def get_dependency_health_matrix():
    """Generate comprehensive dependency health matrix"""
    dependencies = {
        'arcgis_online': {
            'name': 'ArcGIS Online',
            'critical': True,
            'health_check': check_arcgis_health,
            'retry_attempts': 3,
            'timeout_seconds': 10
        },
        'feature_service': {
            'name': 'Feature Service',
            'critical': True,
            'health_check': check_feature_service_health,
            'retry_attempts': 2,
            'timeout_seconds': 15
        },
        'application_insights': {
            'name': 'Application Insights',
            'critical': False,
            'health_check': check_application_insights,
            'retry_attempts': 1,
            'timeout_seconds': 5
        }
    }
    
    health_matrix = {}
    
    for dep_name, config in dependencies.items():
        try:
            health_result = config['health_check']()
            health_matrix[dep_name] = {
                'status': health_result.get('status', 'unknown'),
                'critical': config['critical'],
                'details': health_result
            }
        except Exception as e:
            health_matrix[dep_name] = {
                'status': 'unhealthy',
                'critical': config['critical'],
                'error': str(e)
            }
    
    return health_matrix
```

### Health Check Circuit Breaker

```python
class HealthCheckCircuitBreaker:
    """Circuit breaker pattern for health checks"""
    
    def __init__(self, failure_threshold=3, recovery_timeout=60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, health_check_func):
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = 'HALF_OPEN'
            else:
                return {'status': 'circuit_open', 'error': 'Circuit breaker is open'}
        
        try:
            result = health_check_func()
            if self.state == 'HALF_OPEN':
                self.state = 'CLOSED'
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = 'OPEN'
            
            return {'status': 'unhealthy', 'error': str(e)}
```

## Future Enhancements

### Advanced Health Features
- **Dependency Mapping**: Visual dependency health status
- **Historical Health Trends**: Track health metrics over time
- **Predictive Alerting**: Predict failures based on trends
- **Custom Health Rules**: Configurable health thresholds
- **Integration Testing**: End-to-end workflow validation

### Monitoring Integration
- **Azure Monitor**: Native Azure monitoring integration
- **Prometheus/Grafana**: Custom metrics dashboards
- **PagerDuty**: Automated incident management
- **Slack/Teams**: Health status notifications

### Health Analytics
- **Anomaly Detection**: ML-based health pattern analysis
- **Performance Baselines**: Establish normal operation patterns
- **Capacity Planning**: Predict resource needs based on health trends
- **SLA Monitoring**: Track service level agreement compliance

---

**Implementation Status**: ✅ Complete - Comprehensive health monitoring with ArcGIS connectivity validation, system status reporting, troubleshooting guidance, and detailed metrics collection.