# ACA Spawner for JupyterHub

A JupyterHub spawner that launches single-user notebook servers as Azure Container Apps (ACA).

## Overview

The ACA Spawner (`acaspawner`) enables JupyterHub to dynamically create and manage individual user notebook servers as Azure Container Apps. Each user gets their own isolated container app instance that is automatically provisioned when they log in and destroyed when they log out.

## Features

- **Dynamic provisioning**: Automatically creates Azure Container Apps for each user session
- **Resource control**: Configurable CPU and memory allocations per user
- **Azure integration**: Uses Azure managed identities for secure authentication
- **Auto-scaling**: Supports Azure Container Apps scaling capabilities
- **State management**: Persists container app state across JupyterHub restarts
- **Clean shutdown**: Automatically removes container apps when users stop their servers

## Next Problem to Solve

 - The proxy needs to set the `Host` header to the name of the single-server container-app, because the Azure proxies apparently need that.
 - The JupyterServer (JupyterLab) checks, when establishing a WebSocket connection, whether the Host header matches the expected origin, which it doesn't

```terminaloutput
Blocking Cross Origin API request for /user/marcus/api/events/subscribe.  Origin: https://jupyterhub.mangoflower-dfe0d019.swedencentral.azurecontainerapps.io, Host: aca74ec25afd45e4f3f8f8b3f412c9c3
```

A solution is for sure possible and likely not complex, but not as straightforward as one might think. 
Ultimately, the single-server needs to be made aware of what its front-url is. 
Approaches are:
  - setting the "right" headers in the configurable http proxy
  - configuring the front-url on startup 

## Requirements

- Python 3.7+
- JupyterHub
- Azure subscription with appropriate permissions
- Azure Container Apps environment
- Azure Container Registry (for storing notebook images)
- Azure SDK packages:
  - `azure-identity`
  - `azure-mgmt-appcontainers`

## Configuration

### Required Environment Variables

The spawner requires the following Azure configuration:

```bash
export AZURE_SUBSCRIPTION_ID="your-subscription-id"
export AZURE_RESOURCE_GROUP="your-resource-group"
export AZURE_ACA_ENVIRONMENT_NAME="your-aca-environment-name"
export AZURE_ACR_SERVER="yourregistry.azurecr.io"
export AZURE_ACR_IDENTITY="your-managed-identity-resource-id"
export JUPYTERHUB_HUB_CONNECT_URL="https://your-hub-url"
```

## How It Works

1. **User Login**: When a user logs into JupyterHub and starts their server:
   - The spawner generates a unique ACA name
   - Creates environment variables for JupyterHub communication
   - Provisions an Azure Container App with the configured image and resources

2. **Container Configuration**:
   - Sets up ingress with HTTPS support
   - Configures authentication to Azure Container Registry
   - Passes JupyterHub environment variables to the container
   - Configures the notebook server with proper base URL and security settings

3. **Monitoring**: The spawner polls the container app status to ensure it's running

4. **Shutdown**: When the user stops their server:
   - The spawner deletes the Azure Container App
   - Cleans up all associated resources

## Authentication

The spawner uses `DefaultAzureCredential` for Azure authentication. It will attempt to authenticate using:

1. Environment variables
2. Managed identity (when running in Azure)
3. Other credential sources in the default chain

Ensure the identity has the following permissions:
- `Microsoft.App/containerApps/read`
- `Microsoft.App/containerApps/write`
- `Microsoft.App/containerApps/delete`
- ACR pull permissions via managed identity

## State Management

The spawner persists the following state:
- `aca_running_name`: The name of the currently running container app

This allows JupyterHub to track and manage container apps across restarts.
