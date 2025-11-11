param location string = resourceGroup().location
param projectName string
param stage string
param tags object

resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2022-01-31-preview' = {
  name: 'id-cr-${uniqueString(projectName, stage)}'
  location: location
  tags: tags
}

output managedIdName string = identity.name
output managedIdPrincipalId string = identity.properties.principalId
output managedIdClientId string = identity.properties.clientId
