import os

c = get_config()  # noqa

# dummy for testing. Don't use this in production!
c.JupyterHub.authenticator_class = "dummy"

# launch with docker
c.JupyterHub.spawner_class = "acaspawner.AcaSpawner"

# jupyterhub_config.py (Hub container)
c.JupyterHub.hub_url = "http://127.0.0.1:8081"
c.JupyterHub.bind_url = "http://0.0.0.0:8000"
c.JupyterHub.hub_bind_url = "http://0.0.0.0:8081"

# Publicly reachable URL that single-user servers should use to call back to the Hub
#c.JupyterHub.hub_connect_url = os.environ["JUPYTERHUB_HUB_CONNECT_URL"]
c.JupyterHub.hub_connect_url = "http://0.0.0.0:8081"

c.JupyterHub.trust_xheaders = True
c.JupyterHub.base_url = "/"
c.JupyterHub.cookie_options = {
    "path": "/",          # <— the key bit to stop the loop
    "Secure": False,      # Set to False for internal HTTP communication
    "SameSite": "Lax",    # works well for same-site navigations
}
