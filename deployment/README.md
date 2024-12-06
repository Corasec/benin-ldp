# LDP Deployment  

You will need to configure things by settings the correct environment variables 
in `database/env_vars.env` and `app/env_vars.env` respectively.

## Deploy PostgresSQL

```bash
cd deployment/database/
docker compose up
```

```bash
cd deployment/app/
docker compose up
```

## Build & push the docker image

```bash
cd cosomis/
docker build . -t cosobenin/ldp-app:latest
docker push cosobenin/ldp-app:latest
```

## Deploying the app

```bash
cd deployment/app

docker compose up
```
