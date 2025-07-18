using 'main.bicep'

// Parameters for the ArcGIS function app deployment
param functionAppName = 'simple-func-iac-arcgis-ba'
param storageAccountName = 'sfiacarcgis'
param appInsightsName = 'simple-func-iac-arcgis-ba-insights'
param hostingPlanName = 'simple-func-iac-arcgis-ba-plan'

// ArcGIS Online configuration
param arcgisUrl = 'https://www.arcgis.com'
param arcgisUsername = 'your-arcgis-username'
param arcgisPassword = 'your-arcgis-password'
param featureServiceId = '859582e956e4443c9ebc9c3d84e58d37'  // SensorDataService from notebook
param featureLayerIndex = '0'  // SensorReadings table is at index 0