// Container Apps environment + container app for the literature-triage agent.
//
// Assumes:
// - An existing Container Registry (image pushed there by your CI).
// - An existing Foundry resource/project; this app uses a user-assigned
//   managed identity that the cloud-infra team has granted the
//   "Azure AI Developer" role on the Foundry project.

@description('Azure region. Default to South Central US to match the AI platform.')
param location string = 'southcentralus'

@description('Short app name; used as a prefix for resources.')
param appName string = 'lit-triage-agent'

@description('Full image reference, e.g. myacr.azurecr.io/lit-triage-agent:1.0.0')
param containerImage string

@description('ACR login server hosting the image, e.g. myacr.azurecr.io.')
param acrLoginServer string

@description('Resource ID of the user-assigned managed identity used by the container.')
param userAssignedIdentityResourceId string

@description('Client ID of that same managed identity (passed into the container).')
param userAssignedIdentityClientId string

@description('Foundry project endpoint, e.g. https://<resource>.services.ai.azure.com/api/projects/<project>.')
param projectEndpoint string

@description('Name of the chat-completions deployment, e.g. gpt-4o.')
param modelDeploymentName string

var envName = '${appName}-env'
var appNameFull = appName
var logName = '${appName}-logs'

resource logs 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logName
  location: location
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}

resource env 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: envName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logs.properties.customerId
        sharedKey: logs.listKeys().primarySharedKey
      }
    }
  }
}

resource app 'Microsoft.App/containerApps@2024-03-01' = {
  name: appNameFull
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${userAssignedIdentityResourceId}': {}
    }
  }
  properties: {
    managedEnvironmentId: env.id
    configuration: {
      ingress: {
        external: false  // Only APIM should reach this — keep it internal.
        targetPort: 8000
        transport: 'http'
        allowInsecure: false
      }
      registries: [
        {
          server: acrLoginServer
          identity: userAssignedIdentityResourceId
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'app'
          image: containerImage
          resources: {
            cpu: json('0.5')
            memory: '1.0Gi'
          }
          env: [
            { name: 'AZURE_AI_PROJECT_ENDPOINT',        value: projectEndpoint }
            { name: 'AZURE_AI_MODEL_DEPLOYMENT_NAME',   value: modelDeploymentName }
            { name: 'AZURE_CLIENT_ID',                  value: userAssignedIdentityClientId }
          ]
          probes: [
            {
              type: 'Liveness'
              httpGet: { path: '/healthz', port: 8000 }
              initialDelaySeconds: 10
              periodSeconds: 30
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 5
        rules: [
          {
            name: 'http-scale'
            http: { metadata: { concurrentRequests: '20' } }
          }
        ]
      }
    }
  }
}

output containerAppFqdn string = app.properties.configuration.ingress.fqdn
