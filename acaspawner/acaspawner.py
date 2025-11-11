from azure.identity.aio import DefaultAzureCredential
from azure.mgmt.appcontainers.aio import ContainerAppsAPIClient
from azure.mgmt.appcontainers.models import (
    ContainerApp,
    Configuration,
    Template,
    Container,
    Ingress,
    Scale,
    ContainerResources,
    RegistryCredentials,
    EnvironmentVar,
)
from jupyterhub.spawner import Spawner
from traitlets import default, Unicode, Float, Int
import os
import uuid
import jupyterhub
import asyncio

_jupyterhub_xy = "%i.%i" % (jupyterhub.version_info[:2])

class AcaSpawner(Spawner):
    subscription_id = Unicode(
        config=True,
        help="""Azure subscription ID.
        
        Can be set via AZURE_SUBSCRIPTION_ID environment variable.
        """,
    )

    resource_group = Unicode(
        config=True,
        help="""Azure resource group name.
        
        Can be set via AZURE_RESOURCE_GROUP environment variable.
        """,
    )

    aca_environment_name = Unicode(
        config=True,
        help="""Azure Container Apps environment name.
        
        Can be set via AZURE_ACA_ENVIRONMENT_NAME environment variable.
        """,
    )

    region = Unicode(
        "swedencentral",
        config=True,
        help="""Azure region for the container app.
        
        Can be set via AZURE_REGION environment variable.
        Defaults to 'swedencentral' if not specified.
        """,
    )

    acr_server = Unicode(
        config=True,
        help="""Azure Container Registry server URL.
        
        Can be set via AZURE_ACR_SERVER environment variable.
        """,
    )

    acr_identity = Unicode(
        config=True,
        help="""Azure Container Registry identity for authentication.
        
        Can be set via AZURE_ACR_IDENTITY environment variable.
        """,
    )

    aca_name = Unicode(
        config=True,
        help="""Name for the Azure Container App.
        
        If not specified, will be auto-generated using 'aca' prefix
        and a UUID to ensure uniqueness.
        """,
    )

    cpu = Float(
        1.0,
        config=True,
        help="""CPU allocation for the container.
        
        Specified as a float (e.g., 0.5, 1.0, 2.0).
        """,
    )

    memory = Unicode(
        "2Gi",
        config=True,
        help="""Memory allocation for the container.
        
        Specified as a string with units (e.g., '1Gi', '2Gi', '512Mi').
        """,
    )

    target_port = Int(
        8888,
        config=True,
        help="""Port that the container exposes.
        
        This should match the port that the single-user server
        is listening on inside the container.
        """,
    )

    external_port = Int(
        80,
        config=True,
        help="""External port for the Azure Container App ingress.
        
        This is the port that external traffic will connect to.
        Typically 80 for HTTP or 443 for HTTPS.
        """,
    )

    @default("cmd")
    def _default_cmd(self):
        return "start-notebook.py"

    @default("subscription_id")
    def _default_subscription_id(self):
        return os.getenv("AZURE_SUBSCRIPTION_ID")

    @default("resource_group")
    def _default_resource_group(self):
        return os.getenv("AZURE_RESOURCE_GROUP")

    @default("aca_environment_name")
    def _default_aca_environment_name(self):
        return os.getenv("AZURE_ACA_ENVIRONMENT_NAME")

    @default("region")
    def _default_region(self):
        region = os.getenv("AZURE_REGION")
        if region:
            return region
        return "swedencentral"

    @default("acr_server")
    def _default_acr_server(self):
        return os.getenv("AZURE_ACR_SERVER")

    @default("acr_identity")
    def _default_acr_identity(self):
        return os.getenv("AZURE_ACR_IDENTITY")

    @default("aca_name")
    def _default_aca_name(self):
        # ACA name is first 32 chars of "aca" + uuid without hyphens
        aca_name = "aca" + uuid.uuid4().hex[:29]
        return aca_name

    @default("hub_connect_url")
    def _default_hub_connect_url(self):
        # Return JUPYTERHUB_HUB_CONNECT_URL as the base hub URL
        hub_connect_url = os.getenv("JUPYTERHUB_HUB_CONNECT_URL")
        return hub_connect_url

    aca_running_name = Unicode(allow_none=True)

    @default("image")
    def _default_image(self):
        return f"{self.acr_server}/jupyterhub/singleuser:{_jupyterhub_xy}"

    image = Unicode(
        config=True,
        help="""The image to use for single-user servers.

        This image should have the same version of jupyterhub as
        the Hub itself installed.

        If the default command of the image does not launch
        jupyterhub-singleuser, set ``c.Spawner.cmd`` to
        launch jupyterhub-singleuser, e.g.

        Any of the jupyter docker-stacks should work without additional config,
        as long as the version of jupyterhub in the image is compatible.
        """,
    )

    async def start(self):
        try:
            credential, client = self.get_client()
            environment_id = f"/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group}/providers/Microsoft.App/managedEnvironments/{self.aca_environment_name}"
            self.log.info(
                "Creating ACA %s in environment %s", self.aca_name, environment_id
            )
            hub_env = self.get_env()
            
            # The hub_connect_url should be the external FQDN that containers can reach
            api_url = self.hub_connect_url.rstrip('/') + '/hub/api'
            hub_env["JUPYTERHUB_API_URL"] = api_url
            self.log.info("Setting JUPYTERHUB_API_URL to: %s", api_url)
            
            container = Container(
                name="container",
                image=self.image,
                command=self.cmd if self.cmd else None,
                args=[
                    "--debug",
                    "--ip=0.0.0.0",
                    "--port=8888",
                    "--ServerApp.trust_xheaders=True",
                    "--ServerApp.allow_remote_access=True",
                    "--ServerApp.base_url="
                    + hub_env.get("JUPYTERHUB_SERVICE_PREFIX", "/"),
                ],
                resources=ContainerResources(cpu=self.cpu, memory=self.memory),
            )
            
            # Create environment variables from the corrected hub_env
            container.env = [
                EnvironmentVar(name=k, value=str(v)) for k, v in hub_env.items()
            ]
            
            # Debug logging for key environment variables
            for key in ['JUPYTERHUB_API_URL', 'JUPYTERHUB_API_TOKEN', 'JUPYTERHUB_CLIENT_ID']:
                if key in hub_env:
                    if key == 'JUPYTERHUB_API_TOKEN':
                        # Don't log the full token, just show it exists and length
                        self.log.info("Environment variable %s set (length: %d)", key, len(str(hub_env[key])))
                    else:
                        self.log.info("Environment variable %s: %s", key, hub_env[key])
            
            # Add Azure environment variables
            azure_forward = {
                k: v for k, v in os.environ.items() if k.startswith("AZURE_")
            }
            for k, v in azure_forward.items():
                container.env.append(EnvironmentVar(name=k, value=str(v)))
            app = ContainerApp(
                managed_environment_id=environment_id,
                location=self.region,
                configuration=Configuration(
                    ingress=Ingress(
                        external=True,
                        target_port=self.target_port,
                        allow_insecure=False,
                        traffic=[{"weight": 100, "latest_revision": True}],
                    ),
                    registries=[
                        RegistryCredentials(
                            server=self.acr_server, identity=self.acr_identity
                        )
                    ],
                ),
                template=Template(
                    containers=[container],
                    scale=Scale(min_replicas=1, max_replicas=1),
                ),
            )

            poller = await client.container_apps.begin_create_or_update(
                self.resource_group, self.aca_name, app
            )
            await poller.result()
            self.aca_running_name = self.aca_name
            self.log.info("ACA %s created", self.aca_name)

            # Repeat GET up to 5 times with 1, 2, 4, 8, 16 seconds between attempts
            # Stop when max attempts is reached or fqdn is not None^
            max_attempts = 5
            for attempt in range(max_attempts):
                app = await client.container_apps.get(
                    self.resource_group, self.aca_running_name
                )
                if app.configuration.ingress.fqdn:
                    break
                await asyncio.sleep(2**attempt)
            else:
                raise Exception("Failed to get ACA FQDN")

            #return f"https://{app.configuration.ingress.fqdn}"
            return f"http://{self.aca_name}:8888"

        except Exception as e:
            self.clear_state()
            self.log.error("Error creating ACA %s: %s", self.aca_name, e)
            raise e
        finally:
            if client:
                await client.close()
            if credential:
                await credential.close()

    async def stop(self, now=False):
        try:
            credential, client = self.get_client()
            self.log.info("Deleting ACA %s", self.aca_running_name)
            poller = await client.container_apps.begin_delete(
                self.resource_group, self.aca_running_name
            )
            await poller.result()
            self.clear_state()
            self.log.info("Successfully deleted ACA %s", self.aca_running_name)
        except Exception as e:
            self.log.error("Error deleting ACA %s: %s", self.aca_running_name, e)
            raise e
        finally:
            if client:
                await client.close()
            if credential:
                await credential.close()

    async def poll(self):
        try:
            credential, client = self.get_client()
            self.log.info("Polling ACA %s", self.aca_running_name)
            app = await client.container_apps.get(
                self.resource_group, self.aca_running_name
            )
            if app.provisioning_state != "Succeeded" or app.running_status != "Running":
                return 0
        except Exception as e:
            self.log.error("Error polling ACA %s: %s", self.aca_running_name, e)
            return 0
        finally:
            if client:
                await client.close()
            if credential:
                await credential.close()
        return None

    def load_state(self, state):
        super().load_state(state)
        self.aca_running_name = (
            state.get("aca_running_name", None) or self.aca_running_name
        )

    def get_state(self):
        state = super().get_state()
        state["aca_running_name"] = self.aca_running_name
        return state

    def clear_state(self):
        """Clear the spawner's state"""
        super().clear_state()
        self.aca_running_name = None

    def get_client(self):
        credential = DefaultAzureCredential(
            exclude_environment_credential=False,
            exclude_managed_identity_credential=True,
            exclude_shared_token_cache_credential=True,
            exclude_visual_studio_credential=True,
            exclude_visual_studio_code_credential=True,
            exclude_azure_cli_credential=True,
            exclude_interactive_browser_credential=True,
        )
        client = ContainerAppsAPIClient(
            credential=credential, subscription_id=self.subscription_id
        )
        return [credential, client]
