using 'main.bicep'

// Non-secret values live here. Secrets come from environment variables, never from the repo.
param appName = readEnvironmentVariable('APP_NAME', 'cisonauti-booking')
param image = readEnvironmentVariable('IMAGE')
param adminEmail = readEnvironmentVariable('ADMIN_EMAIL')

param sqlAdminPassword = readEnvironmentVariable('SQL_ADMIN_PASSWORD')
param secretKey = readEnvironmentVariable('SECRET_KEY')
param adminPassword = readEnvironmentVariable('ADMIN_PASSWORD', '')
param ghcrUsername = readEnvironmentVariable('GHCR_USERNAME', '')
param ghcrToken = readEnvironmentVariable('GHCR_TOKEN', '')
