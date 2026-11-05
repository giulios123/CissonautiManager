// Cisonauti Booking on Azure: one Container App (scales to zero) + Azure SQL Basic.
// Deploy at resource group scope: az deployment group create -g <rg> -f infra/main.bicep -p infra/main.bicepparam

targetScope = 'resourceGroup'

@description('Short name used for all resources (lowercase letters, digits, hyphens).')
@minLength(3)
@maxLength(20)
param appName string

param location string = resourceGroup().location

@description('Optional region for the SQL server, for when the main region does not accept new SQL servers. Empty means the same as location.')
param sqlLocation string = ''

@description('Full image reference, for example ghcr.io/owner/repo:abc123.')
param image string

param sqlAdminLogin string = 'cisonautiadmin'

@secure()
param sqlAdminPassword string

@secure()
param secretKey string

@description('Email of the first admin, created at startup.')
param adminEmail string

@description('Optional: lets the first admin log in with a password right away.')
@secure()
param adminPassword string = ''

@description('Optional: only needed when the GitHub package is private.')
param ghcrUsername string = ''

@secure()
param ghcrToken string = ''

@description('console writes emails to the logs; real email arrives with MVP 2.')
param emailProvider string = 'console'

var unique = uniqueString(resourceGroup().id)
var sqlServerName = '${appName}-sql-${unique}'
var sqlRegion = empty(sqlLocation) ? location : sqlLocation
var databaseName = 'cisonauti'

resource logs 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${appName}-logs'
  location: location
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}

resource environment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: '${appName}-env'
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

resource sqlServer 'Microsoft.Sql/servers@2023-08-01-preview' = {
  name: sqlServerName
  location: sqlRegion
  properties: {
    administratorLogin: sqlAdminLogin
    administratorLoginPassword: sqlAdminPassword
    minimalTlsVersion: '1.2'
    publicNetworkAccess: 'Enabled'
  }
}

// 0.0.0.0 means "Azure services": lets the Container App reach the server.
resource allowAzureServices 'Microsoft.Sql/servers/firewallRules@2023-08-01-preview' = {
  parent: sqlServer
  name: 'AllowAzureServices'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

// Basic tier: about 5 EUR/month, always on, 2 GB (decision D-007).
resource database 'Microsoft.Sql/servers/databases@2023-08-01-preview' = {
  parent: sqlServer
  name: databaseName
  location: sqlRegion
  sku: {
    name: 'Basic'
    tier: 'Basic'
    capacity: 5
  }
  properties: {
    maxSizeBytes: 2147483648
    collation: 'SQL_Latin1_General_CP1_CI_AS'
  }
}

var databaseUrl = 'mssql+pyodbc://${sqlAdminLogin}:${uriComponent(sqlAdminPassword)}@${sqlServer.properties.fullyQualifiedDomainName}:1433/${databaseName}?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no'

var baseSecrets = [
  { name: 'database-url', value: databaseUrl }
  { name: 'secret-key', value: secretKey }
]
var adminSecrets = empty(adminPassword) ? [] : [{ name: 'admin-password', value: adminPassword }]
var registrySecrets = empty(ghcrToken) ? [] : [{ name: 'ghcr-token', value: ghcrToken }]

var baseEnv = [
  { name: 'APP_ENV', value: 'production' }
  { name: 'APP_BASE_URL', value: 'https://${appName}.${environment.properties.defaultDomain}' }
  { name: 'ADMIN_EMAIL', value: adminEmail }
  { name: 'EMAIL_PROVIDER', value: emailProvider }
  { name: 'DATABASE_URL', secretRef: 'database-url' }
  { name: 'SECRET_KEY', secretRef: 'secret-key' }
]
var adminEnv = empty(adminPassword) ? [] : [{ name: 'ADMIN_PASSWORD', secretRef: 'admin-password' }]

resource app 'Microsoft.App/containerApps@2024-03-01' = {
  name: appName
  location: location
  properties: {
    managedEnvironmentId: environment.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
        allowInsecure: false
      }
      secrets: concat(baseSecrets, adminSecrets, registrySecrets)
      registries: empty(ghcrToken) ? [] : [
        {
          server: 'ghcr.io'
          username: ghcrUsername
          passwordSecretRef: 'ghcr-token'
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'app'
          image: image
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
          env: concat(baseEnv, adminEnv)
          probes: [
            {
              // Migrations run before the server starts, so allow a long start.
              type: 'Startup'
              httpGet: { path: '/api/health', port: 8000 }
              initialDelaySeconds: 3
              periodSeconds: 3
              failureThreshold: 40
            }
            {
              type: 'Liveness'
              httpGet: { path: '/api/health', port: 8000 }
              periodSeconds: 30
            }
          ]
        }
      ]
      scale: {
        // Scale to zero when nobody uses the app. One replica at most: migrations run at
        // startup and must not race each other.
        minReplicas: 0
        maxReplicas: 1
        rules: [
          {
            name: 'http'
            http: { metadata: { concurrentRequests: '20' } }
          }
        ]
      }
    }
  }
  dependsOn: [
    database
    allowAzureServices
  ]
}

output url string = 'https://${app.properties.configuration.ingress.fqdn}'
output sqlServer string = sqlServer.properties.fullyQualifiedDomainName
