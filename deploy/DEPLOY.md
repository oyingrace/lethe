# Deploying Lethe to Alibaba Cloud ECS

Phase 0 exit criteria: `curl http://<ecs-ip>/qwen-check` returns a real
Qwen-generated sentence. Do this before any feature work (see BUILD_PLAN.md
§6) — if ECS or DashScope access is going to be a problem, find out at hour 2,
not hour 46.

## 1. Provision the instance

1. Create an ECS instance (Ubuntu 22.04, smallest size that runs Docker
   comfortably — 2 vCPU / 4 GiB is plenty for the skeleton).
2. Open inbound ports in the security group: 22 (SSH), 8000 (API), and 80/443
   if you bring up the optional Caddy proxy.
3. SSH in and install Docker + the Compose plugin:
   ```bash
   curl -fsSL https://get.docker.com | sh
   sudo usermod -aG docker $USER
   # log out/in (or `newgrp docker`) for the group change to apply
   docker compose version
   ```

## 2. Get the code and secrets onto the box

```bash
git clone <this-repo-url> lethe
cd lethe/deploy
cp .env.example .env
# edit .env: paste QWEN_API_KEY, confirm MODEL_* names match your DashScope
# access, and pick a POSTGRES_PASSWORD
```

Get a DashScope API key from the Alibaba Cloud Model Studio console; the
model IDs (MODEL_FAST/MODEL_REASONING/MODEL_EMBED/MODEL_RERANK) come from
whatever your account has access to — never hardcode them elsewhere.

## 3. Bring the skeleton up

```bash
docker compose up -d --build
docker compose ps          # postgres should be "healthy", server "running"
curl http://localhost:8000/health
curl http://localhost:8000/qwen-check
```

`/qwen-check` should return `{"degraded": false, "model": "...", "text": "...",
"usage": {...}}`. If it returns `{"degraded": true, "error": "..."}`, check
`docker compose logs server` — usually a missing/incorrect `QWEN_API_KEY` or
`MODEL_FAST` env var, or the DashScope endpoint being unreachable from the
region the ECS instance is in.

From your own machine (not the ECS box):

```bash
curl http://<ecs-public-ip>:8000/qwen-check
```

## 4. Optional: put Caddy in front

Once you have a domain pointed at the ECS instance's IP:

```bash
docker compose --profile proxy up -d
```

This starts Caddy reverse-proxying port 80 (and 443 once you add a real
domain to the `Caddyfile`) to the `server` container.

## 5. Redeploy

Every later phase ends with a redeploy — by Phase 2 this should be routine:

```bash
git pull
docker compose up -d --build
curl http://localhost:8000/health
```

## Fallback

If ECS is blocked outright (account verification, coupon, region, endpoint
reachability), the documented fallback is Alibaba Cloud SAE or a different
region — decide this at hour 2, not hour 46 (BUILD_PLAN.md §9).
