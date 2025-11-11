ARG JUPYTERHUB_VERSION=5.4
FROM jupyterhub/jupyterhub:$JUPYTERHUB_VERSION
COPY requirements.txt /tmp/requirements.txt
RUN python3 -m pip install --no-cache -r /tmp/requirements.txt
COPY pyproject.toml /srv/acaspawner/pyproject.toml
COPY acaspawner /srv/acaspawner/acaspawner
RUN python3 -m pip install --no-cache -e /srv/acaspawner
COPY jupyterhub_config.py /srv/jupyterhub/jupyterhub_config.py

# Create directory for cookie secret and set permissions
RUN mkdir -p /srv/jupyterhub && \
    openssl rand -hex 32 > /srv/jupyterhub/cookie_secret && \
    chmod 600 /srv/jupyterhub/cookie_secret
