# HD Domain Deployment Notes

Production domain:

```text
https://hd.yxck3d.tech
```

GitHub repository:

```text
https://github.com/reynold2/hd.git
```

The HD deployment is isolated from the existing SaaS project and other projects on the same server.

## Isolation Map

Do not reuse any `yuyue-saas` directory, service, or port.

| Item | HD value |
| --- | --- |
| App directory | `/www/dk_project/wwwroot/hd` |
| Backend service | `hd-queue.service` |
| Backend port | `127.0.0.1:8020` |
| Backend database | `/www/dk_project/wwwroot/hd/data/queue_calling.db` |
| Nginx vhost | `/www/server/panel/vhost/nginx/hd.yxck3d.tech.conf` |
| Merchant admin | `https://hd.yxck3d.tech/admin/` |
| Customer H5 | `https://hd.yxck3d.tech/customer/` |
| API | `https://hd.yxck3d.tech/api/` |

## Manual Deploy

Run on `8.141.105.10`:

```bash
cd /www/dk_project/wwwroot/hd
bash deploy/hd/deploy.sh
```

For the first deploy, if `/www/dk_project/wwwroot/hd` does not exist yet:

```bash
mkdir -p /www/dk_project/wwwroot
git clone https://github.com/reynold2/hd.git /www/dk_project/wwwroot/hd
cd /www/dk_project/wwwroot/hd
bash deploy/hd/deploy.sh
```

If GitHub asks for private repository credentials, put a token with repository read access here:

```text
/root/.config/hd-queue/github_token
```

The script will:

1. Pull `main` from `https://github.com/reynold2/hd.git`.
2. Install backend dependencies in `/www/dk_project/wwwroot/hd/backend/.venv`.
3. Run Alembic migrations against the isolated SQLite database.
4. Install and restart `hd-queue.service`.
5. Build merchant admin with `VITE_API_BASE=/api` and base `/admin/`.
6. Build customer H5 with `VITE_API_BASE=/api` and base `/customer/`.
7. Optionally build WeChat miniapp with `VITE_API_BASE=https://hd.yxck3d.tech` when `SKIP_MINIAPP_BUILD=0`.
8. Ensure an isolated origin certificate exists under `/www/server/panel/vhost/letsencrypt/hd.yxck3d.tech`.
9. Copy `deploy/hd/nginx-hd.yxck3d.tech.conf` into the Nginx vhost directory.
10. Run `nginx -t`, reload Nginx, and verify health URLs.

## WeChat Mini Program Domain Checklist

In WeChat Mini Program admin, add the following legal request domain:

```text
https://hd.yxck3d.tech
```

The miniapp production build uses:

```bash
VITE_API_BASE=https://hd.yxck3d.tech npm run build:mp-weixin
```

The H5 customer app uses same-origin API requests:

```text
https://hd.yxck3d.tech/customer/
https://hd.yxck3d.tech/api/
```

## Cloudflare / SSL

DNS record:

```text
hd.yxck3d.tech A 8.141.105.10 proxied
```

Because Cloudflare is proxied, the public HTTPS certificate is provided by Cloudflare. The deploy script also ensures the origin has an isolated `hd.yxck3d.tech` certificate so HTTPS requests from Cloudflare hit the HD 443 vhost instead of another site's default vhost. If switching to Full (strict), replace the generated origin certificate with a Cloudflare Origin Certificate or another certificate trusted by Cloudflare strict mode.

## Checks

```bash
systemctl status hd-queue.service --no-pager -l
curl -i http://127.0.0.1:8020/health
curl -i http://hd.yxck3d.tech/health
curl -I http://hd.yxck3d.tech/admin/
curl -I http://hd.yxck3d.tech/customer/
```
