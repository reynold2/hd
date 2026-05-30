# FH Deployment Notes

Production server:

```text
8.141.105.10
```

The deployment is isolated from the existing `yuyue-saas` service:

- Backend service: `fh-queue.service`
- Backend port: `127.0.0.1:8021`
- Backend path: `/www/dk_project/wwwroot/fh/backend`
- SQLite data path: `/www/dk_project/wwwroot/fh/data/queue_calling.db`
- Merchant admin static path: `/www/wwwroot/fh/admin`
- Customer H5 static path: `/www/wwwroot/fh/customer`
- Nginx include: `/www/server/panel/vhost/nginx/extension/8.141.105.10/fh.conf`

Public URLs:

```text
http://8.141.105.10/fh/admin/
http://8.141.105.10/fh/customer/
http://8.141.105.10/fh/health
```

Build with the isolated API base:

```powershell
cd D:\3d\fh\merchant-admin
$env:VITE_API_BASE='/fh'
npm.cmd run build -- --base=/fh/admin/

cd D:\3d\fh\customer-miniapp
$env:VITE_API_BASE='/fh'
npm.cmd run build:h5 -- --base=/fh/customer/
```

Service checks:

```bash
systemctl status fh-queue.service --no-pager -l
curl -i http://127.0.0.1:8021/health
curl -i -H 'Host: 8.141.105.10' http://127.0.0.1/fh/health
```

Do not reuse `127.0.0.1:8010`, `/www/dk_project/wwwroot/yuyue-saas`, or `yuyue-saas.service`; those belong to the SaaS project.
