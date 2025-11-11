param location string = resourceGroup().location
param projectName string
param stage string
param tags object
param managedIdPrincipalId string
param adminPrincipalId string

module acrModule './container-registry.bicep' = {
  name: '${deployment().name}-container-registry'
  params: {
    location: location
    projectName: projectName
    stage: stage
    managedIdPrincipalId: managedIdPrincipalId
    adminPrincipalId: adminPrincipalId
    tags: tags
  }
}

module workspaceModule './log-workspace.bicep' = {
  name: '${deployment().name}-workspace'
  params: {
    location: location
    projectName: projectName
    stage: stage
    tags: tags
  }
}

module containerAppsEnv './container-apps-env.bicep' = {
  name: '${deployment().name}-container-apps-env'
  params: {
    location: location
    projectName: projectName
    stage: stage
    tags: tags
    logAnalyticsWorkspaceName: workspaceModule.outputs.workspaceName
  }
}

output registryName string = acrModule.outputs.registryName
output workspaceName string = workspaceModule.outputs.workspaceName
output workspaceId string = workspaceModule.outputs.workspaceId
output environmentName string = containerAppsEnv.outputs.environmentName
