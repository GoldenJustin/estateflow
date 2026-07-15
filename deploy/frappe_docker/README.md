# Permanent EstateFlow deployment on Frappe Docker

Do not install EstateFlow only inside a running backend container. Backend, frontend, websocket, scheduler and queue services must use one image containing the same apps and assets.

## 1. Push the release

Push EstateFlow and Logistics Management branches referenced by `apps.json` before building.

## 2. Copy the app manifest

From the `frappe_docker` repository root:

```bash
cp /path/to/estateflow/deploy/frappe_docker/apps.json ./apps.json
python3 -m json.tool apps.json >/dev/null
```

## 3. Build the version-16 image

Use Docker BuildKit secrets so repository credentials are not exposed in image history:

```bash
docker build \
  --no-cache \
  --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
  --build-arg=FRAPPE_BRANCH=version-16 \
  --secret=id=apps_json,src=apps.json \
  --tag=golden-erpnext:16-estateflow-0.1.5 \
  --file=images/layered/Containerfile \
  .
```

## 4. Select the image

Add to the environment file used by Docker Compose:

```text
CUSTOM_IMAGE=golden-erpnext
CUSTOM_TAG=16-estateflow-0.1.5
PULL_POLICY=never
```

Recreate the existing stack with the same compose files and environment file. Do not use `docker compose down -v`; the `-v` option removes site/database volumes.

```bash
docker compose --env-file custom.env [YOUR EXISTING -f FILES] up -d --force-recreate
```

## 5. Migrate and verify

```bash
docker exec -it frappe_docker-backend-1 bash -lc '
cd /home/frappe/frappe-bench &&
bench --site mysite.localhost migrate &&
bench --site mysite.localhost clear-cache &&
bench --site mysite.localhost list-apps
'

docker ps
```

Backend, frontend, websocket, queue-short, queue-long and scheduler must all remain `Up`.

Verify permanent CSS from the host:

```bash
BASE_URL=http://127.0.0.1:8080
curl -sSI "$BASE_URL/assets/estateflow/css/estateflow.css?v=0.1.5" | grep -Ei 'HTTP/|content-type'
curl -sSI "$BASE_URL/assets/estateflow/css/estateflow-guide.css?v=0.1.5" | grep -Ei 'HTTP/|content-type'
```

Both responses must be `200` and `text/css`. Restarting any service will remain safe because the custom image contains EstateFlow and all assets.
