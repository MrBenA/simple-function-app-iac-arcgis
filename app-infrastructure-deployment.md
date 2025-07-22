# Infrastructure Deployment Feature

## Overview

The infrastructure deployment feature provides Infrastructure as Code (IaC) capabilities using Azure Bicep templates for automated deployment of Azure Function App resources and related services. This feature ensures consistent, repeatable deployments with integrated ArcGIS Online configuration and monitoring capabilities.

## Infrastructure Components

### Core Azure Resources

The Bicep template deploys the following Azure resources:

1. **Azure Function App**: Linux-based serverless compute platform
2. **Storage Account**: Function app storage with unique naming
3. **Application Insights**: Monitoring and telemetry collection
4. **App Service Plan**: Consumption (serverless) hosting plan

### Resource Configuration

#### Function App Configuration
- **Runtime**: Python 3.9 (configurable)
- **Platform**: Linux (required for Python runtime)
- **Plan Type**: Consumption (Y1 SKU) for cost-effective serverless execution
- **Extensions Version**: ~4 (latest Azure Functions runtime)

#### Storage Account Configuration
- **Type**: StorageV2 with Standard_LRS replication
- **Security**: HTTPS-only traffic with minimum TLS 1.2
- **Naming**: Unique suffix generated using resource group ID

#### Application Insights Configuration
- **Type**: Web application monitoring
- **Integration**: Connected via instrumentation key and connection string
- **Request Source**: REST API optimized

## Bicep Template Structure

### Parameters

The template accepts the following parameters:

| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| `functionAppName` | string | ✅ | Function App name | - |
| `location` | string | ❌ | Deployment location | Resource Group location |
| `storageAccountName` | string | ✅ | Storage account base name | - |
| `appInsightsName` | string | ✅ | Application Insights name | - |
| `hostingPlanName` | string | ✅ | App Service Plan name | - |
| `arcgisUrl` | string | ❌ | ArcGIS Online URL | https://www.arcgis.com |
| `arcgisUsername` | string | ✅ | ArcGIS Online username | - |
| `arcgisPassword` | string | ✅ | ArcGIS Online password | - |
| `featureServiceId` | string | ✅ | ArcGIS Feature Service ID | - |
| `featureLayerIndex` | string | ❌ | Layer index in service | "0" |

### Resource Definitions

#### Storage Account Resource
```bicep
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: uniqueStorageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
  }
}
```

#### Function App Resource
```bicep
resource functionApp 'Microsoft.Web/sites@2023-01-01' = {
  name: functionAppName
  location: location
  kind: 'functionapp,linux'
  properties: {
    serverFarmId: hostingPlan.id
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.9'
      appSettings: [
        // Standard Azure Functions settings
        // ArcGIS integration settings
      ]
    }
  }
}
```

### Environment Variables Configuration

The template automatically configures the following environment variables:

#### Azure Functions Standard Settings
- `AzureWebJobsStorage`: Storage account connection string
- `WEBSITE_CONTENTAZUREFILECONNECTIONSTRING`: Content storage connection
- `WEBSITE_CONTENTSHARE`: Unique content share name
- `FUNCTIONS_EXTENSION_VERSION`: Functions runtime version (~4)
- `FUNCTIONS_WORKER_RUNTIME`: Python runtime specification
- `PYTHON_ENABLE_WORKER_EXTENSIONS`: Enable worker extensions

#### Application Insights Integration
- `APPINSIGHTS_INSTRUMENTATIONKEY`: Legacy instrumentation key
- `APPLICATIONINSIGHTS_CONNECTION_STRING`: Modern connection string

#### ArcGIS Online Integration
- `ARCGIS_URL`: ArcGIS Online organization URL
- `ARCGIS_USERNAME`: Authentication username
- `ARCGIS_PASSWORD`: Authentication password (secure parameter)
- `FEATURE_SERVICE_ID`: Target feature service identifier
- `FEATURE_LAYER_INDEX`: Layer index within service

## Parameter File Configuration

### main.bicepparam Example

```bicep
using 'main.bicep'

// Basic Azure resource naming
param functionAppName = 'simple-func-iac-arcgis-ba'
param storageAccountName = 'sfiacarcgis'
param appInsightsName = 'simple-func-iac-arcgis-ba-insights'
param hostingPlanName = 'simple-func-iac-arcgis-ba-plan'

// ArcGIS Online integration
param arcgisUrl = 'https://www.arcgis.com'
param arcgisUsername = 'your-arcgis-username'
param arcgisPassword = 'your-arcgis-password'
param featureServiceId = '859582e956e4443c9ebc9c3d84e58d37'
param featureLayerIndex = '0'
```

### Parameter Configuration Guidelines

1. **Resource Naming**:
   - Use consistent naming convention across resources
   - Include environment identifier (dev, test, prod)
   - Keep names under Azure limits (24 chars for storage accounts)

2. **ArcGIS Configuration**:
   - Use actual ArcGIS Online credentials (not placeholders)
   - Verify feature service ID exists and is accessible
   - Confirm layer index corresponds to target table

3. **Security Considerations**:
   - Store sensitive parameters in Azure Key Vault for production
   - Use parameter files with secure parameters for deployment
   - Never commit credentials to source control

## Deployment Methods

### Azure CLI Deployment

#### Manual Deployment Command
```bash
# Navigate to infrastructure directory
cd infra

# Validate template
az deployment group validate \
  --resource-group rg-simple-func-iac-arcgis \
  --template-file main.bicep \
  --parameters main.bicepparam

# Deploy infrastructure
az deployment group create \
  --resource-group rg-simple-func-iac-arcgis \
  --template-file main.bicep \
  --parameters main.bicepparam
```

#### Deployment with Parameter Override
```bash
az deployment group create \
  --resource-group rg-simple-func-iac-arcgis \
  --template-file main.bicep \
  --parameters main.bicepparam \
  --parameters arcgisUsername="actual-username" \
  --parameters arcgisPassword="actual-password"
```

### Azure PowerShell Deployment

```powershell
# Validate template
Test-AzResourceGroupDeployment `
  -ResourceGroupName "rg-simple-func-iac-arcgis" `
  -TemplateFile "main.bicep" `
  -TemplateParameterFile "main.bicepparam"

# Deploy infrastructure
New-AzResourceGroupDeployment `
  -ResourceGroupName "rg-simple-func-iac-arcgis" `
  -TemplateFile "main.bicep" `
  -TemplateParameterFile "main.bicepparam"
```

## GitHub Actions Integration (Future Enhancement)

### Planned Workflow Structure

The project is designed to support GitHub Actions workflows for automated deployment:

#### Infrastructure Deployment Workflow
```yaml
name: Deploy Infrastructure
on:
  push:
    paths:
      - 'infra/**'
  workflow_dispatch:
    inputs:
      environment:
        description: 'Target environment'
        required: true
        default: 'dev'

jobs:
  deploy-infrastructure:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Azure Login
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}
      
      - name: Deploy Bicep Template
        uses: azure/CLI@v1
        with:
          inlineScript: |
            az deployment group create \
              --resource-group ${{ secrets.AZURE_RESOURCE_GROUP }} \
              --template-file infra/main.bicep \
              --parameters infra/main.bicepparam \
              --parameters arcgisUsername="${{ secrets.ARCGIS_USERNAME }}" \
              --parameters arcgisPassword="${{ secrets.ARCGIS_PASSWORD }}"
```

#### Application Deployment Workflow
```yaml
name: Deploy Function App
on:
  push:
    paths:
      - 'src/**'
  workflow_dispatch:

jobs:
  deploy-app:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd src
          pip install -r requirements.txt
      
      - name: Deploy to Azure Functions
        uses: Azure/functions-action@v1
        with:
          app-name: ${{ secrets.FUNCTION_APP_NAME }}
          package: 'src'
          publish-profile: ${{ secrets.AZURE_FUNCTIONAPP_PUBLISH_PROFILE }}
```

### Required GitHub Secrets

For automated deployment, configure these repository secrets:

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `AZURE_CREDENTIALS` | Service principal JSON | `{"clientId": "...", "clientSecret": "..."}` |
| `AZURE_RESOURCE_GROUP` | Target resource group | `rg-simple-func-iac-arcgis` |
| `FUNCTION_APP_NAME` | Function app name | `simple-func-iac-arcgis-ba` |
| `ARCGIS_USERNAME` | ArcGIS Online username | `your-username` |
| `ARCGIS_PASSWORD` | ArcGIS Online password | `your-password` |
| `AZURE_FUNCTIONAPP_PUBLISH_PROFILE` | Function app publish profile | Download from Azure Portal |

## Deployment Validation

### Post-Deployment Verification

After successful deployment, verify the following:

1. **Resource Creation**:
   ```bash
   # List deployed resources
   az resource list --resource-group rg-simple-func-iac-arcgis --output table
   ```

2. **Function App Status**:
   ```bash
   # Check function app status
   az functionapp show --name simple-func-iac-arcgis-ba \
     --resource-group rg-simple-func-iac-arcgis \
     --query "state"
   ```

3. **Environment Variables**:
   ```bash
   # Verify ArcGIS configuration
   az functionapp config appsettings list \
     --name simple-func-iac-arcgis-ba \
     --resource-group rg-simple-func-iac-arcgis \
     --query "[?contains(name, 'ARCGIS')].{Name:name, Value:value}"
   ```

4. **Health Check**:
   ```bash
   # Test health endpoint
   curl https://simple-func-iac-arcgis-ba.azurewebsites.net/api/health
   ```

## Troubleshooting

### Common Deployment Issues

#### 1. Storage Account Name Conflicts
**Problem**: Storage account name already exists globally
**Solution**: 
- Modify `storageAccountName` parameter to use a more unique prefix
- The template adds a unique suffix, but base name must be unique

#### 2. Parameter Validation Failures
**Problem**: Missing or invalid required parameters
**Solution**:
- Verify all required parameters are provided in .bicepparam file
- Check parameter types match template definitions
- Ensure secure parameters are properly marked

#### 3. ArcGIS Authentication Issues
**Problem**: Invalid ArcGIS credentials during deployment
**Solution**:
- Verify credentials work with ArcGIS Online portal
- Check if account requires 2FA (not supported for service accounts)
- Ensure feature service ID exists and is accessible

#### 4. Linux Function App Issues
**Problem**: Function app fails to start on Linux
**Solution**:
- Verify Python version compatibility (3.9, 3.10, or 3.11)
- Check that `reserved: true` is set for Linux hosting plan
- Ensure `FUNCTIONS_WORKER_RUNTIME` is set to "python"

### Deployment Logs and Monitoring

#### View Deployment Progress
```bash
# Monitor deployment status
az deployment group show \
  --resource-group rg-simple-func-iac-arcgis \
  --name main \
  --query "properties.provisioningState"

# View deployment operations
az deployment operation group list \
  --resource-group rg-simple-func-iac-arcgis \
  --name main
```

#### Function App Logs
```bash
# Enable logging
az functionapp log config \
  --name simple-func-iac-arcgis-ba \
  --resource-group rg-simple-func-iac-arcgis \
  --application-logging true

# Stream live logs
az functionapp log tail \
  --name simple-func-iac-arcgis-ba \
  --resource-group rg-simple-func-iac-arcgis
```

## Security Best Practices

### Parameter Security

1. **Secure Parameters**: Mark sensitive parameters with `@secure()` decorator
2. **Key Vault Integration**: Use Azure Key Vault for production credentials
3. **Parameter Files**: Never commit files containing actual credentials
4. **Environment Separation**: Use different parameter files per environment

### Access Control

1. **Service Principals**: Use dedicated service principals for deployments
2. **RBAC**: Configure Role-Based Access Control for resource groups
3. **Network Security**: Consider VNet integration for production deployments
4. **Managed Identity**: Plan migration to managed identity authentication

### Example Key Vault Integration

```bicep
// Future enhancement: Key Vault reference
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: 'kv-simple-func-arcgis'
  scope: resourceGroup('rg-keyvault')
}

// Reference secrets from Key Vault
{
  name: 'ARCGIS_USERNAME'
  value: '@Microsoft.KeyVault(SecretUri=${keyVault.properties.vaultUri}secrets/arcgis-username/)'
}
```

## Cost Optimization

### Resource Sizing

- **Consumption Plan**: Pay-per-execution model with generous free tier
- **Storage Account**: Standard_LRS provides cost-effective local redundancy
- **Application Insights**: Sampling and data retention policies to control costs

### Cost Monitoring

```bash
# View resource costs
az consumption usage list \
  --scope "/subscriptions/{subscription-id}/resourceGroups/rg-simple-func-iac-arcgis" \
  --start-date 2024-01-01 \
  --end-date 2024-01-31
```

## Future Enhancements

### Planned Infrastructure Improvements

1. **Multi-Environment Support**: Environment-specific parameter files
2. **Container Deployment**: Support for containerized function apps
3. **VNet Integration**: Private networking for enhanced security
4. **Monitoring Alerts**: Automated alerting for resource health
5. **Backup Strategy**: Automated backup for function app configuration

### GitOps Integration

1. **Pull Request Workflows**: Infrastructure change validation
2. **Environment Promotion**: Automated promotion between environments  
3. **Rollback Capabilities**: Infrastructure rollback procedures
4. **Compliance Scanning**: Security and compliance policy enforcement

---

**Implementation Status**: ✅ Complete - Production-ready Infrastructure as Code with Bicep templates for automated Azure Function App deployment with integrated ArcGIS Online configuration.