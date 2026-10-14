# Apache Jena Fuseki (Docker)

This folder contains a Docker setup for running Apache Jena Fuseki using a custom multi-stage Docker build.

The image:

- Downloads and verifies the official Apache Fuseki distribution
- Runs Fuseki via the fuseki-server script (not a single JAR)
- Uses a non-root user
- Persists data under /fuseki
- Includes tini and a custom docker-entrypoint.sh
- Supports basic authentication via shiro.ini
- Automatically creates datasets defined via `FUSEKI_DATASET_*` environment variables

## Run with Docker Compose

A minimal docker-compose-fuseki.yml is provided in this folder. 

Before starting, create the password secret file:

```shell
echo "yourpassword" > secrets/ADMIN_PASSWORD.txt
```

Then start the container:

```shell
docker compose -f docker-compose-fuseki.yml up --build
```

Fuseki will be available at: <http://localhost:3030>

## Data persistence

All datasets, configuration, and logs are stored in the Docker volume: ` /fuseki `

This ensures data survives container restarts.

## Authentication

Basic authentication is enabled via `shiro.ini`. The admin password is read from the Docker secret at `secrets/ADMIN_PASSWORD.txt`.

On every startup, the entrypoint hashes the plaintext password using the Shiro argon2id hasher and writes it into `shiro.ini`.

### Changing the

1. Update `secrets/ADMIN_PASSWORD.txt` with the new password
2. Restart the container — the new hash is generated and applied automatically

## Datasets

The datasets to create are configured via `FUSEKI_DATASET_*` environment variables in `docker-compose-fuseki.yml`. On startup the entrypoint waits for Fuseki to be ready and then creates each dataset automatically.
