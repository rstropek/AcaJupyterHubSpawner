param location string = resourceGroup().location
param projectName string
param stage string
param tags object
param logAnalyticsWorkspaceName string

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' existing = {
  name: logAnalyticsWorkspaceName
}
resource vnet 'Microsoft.Network/virtualNetworks@2023-09-01' existing = {
  name: 'vnet-jupyter'
}
resource infraSubnet 'Microsoft.Network/virtualNetworks/subnets@2023-09-01' existing = {
  parent: vnet
  name: 'default'
}

// Create container apps environment
resource environment 'Microsoft.App/managedEnvironments@2025-01-01' = {
  name: 'cae-${uniqueString(projectName, stage)}'
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
    workloadProfiles: [
      {
        name: 'Consumption'
        workloadProfileType: 'Consumption'
      }
    ]
    vnetConfiguration: {
          infrastructureSubnetId: infraSubnet.id
          // Optional settings:
          // internal: true // to expose environment with internal load balancer only
          // dockerBridgeCidr: '172.17.0.1/16'
          // platformReservedCidr: '172.16.0.0/16'
          // platformReservedDnsIP: '172.16.0.10'
        }
  }
}

output environmentName string = environment.name
