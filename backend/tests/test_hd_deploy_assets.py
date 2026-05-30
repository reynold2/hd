from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_hd_deploy_script_uses_isolated_defaults():
    script = ROOT / "deploy" / "hd" / "deploy.sh"
    assert script.exists()
    content = script.read_text(encoding="utf-8")

    assert 'APP_DIR="${APP_DIR:-/www/dk_project/wwwroot/hd}"' in content
    assert 'REPO_URL="${REPO_URL:-https://github.com/reynold2/hd.git}"' in content
    assert 'SERVICE_NAME="${SERVICE_NAME:-hd-queue.service}"' in content
    assert 'DOMAIN="${DOMAIN:-hd.yxck3d.tech}"' in content
    assert 'BACKEND_PORT="${BACKEND_PORT:-8020}"' in content
    assert "ensure_origin_cert" in content
    assert "/www/server/panel/vhost/letsencrypt/hd.yxck3d.tech" in content
    assert "/www/dk_project/wwwroot/yuyue-saas" not in content
    assert "yuyue-saas.service" not in content


def test_hd_nginx_conf_uses_domain_root_and_dedicated_backend():
    nginx_conf = ROOT / "deploy" / "hd" / "nginx-hd.yxck3d.tech.conf"
    assert nginx_conf.exists()
    content = nginx_conf.read_text(encoding="utf-8")

    assert "server_name hd.yxck3d.tech;" in content
    assert "listen 443 ssl;" in content
    assert "ssl_certificate /www/server/panel/vhost/letsencrypt/hd.yxck3d.tech/fullchain.pem;" in content
    assert "proxy_pass http://127.0.0.1:8020/api/;" in content
    assert "alias /www/dk_project/wwwroot/hd/merchant-admin/dist/;" in content
    assert "alias /www/dk_project/wwwroot/hd/customer-miniapp/dist/build/h5/;" in content
    assert "saas.yxck3d.tech" not in content
    assert "127.0.0.1:8010" not in content


def test_hd_deploy_builds_wechat_miniapp_by_default_and_checks_only_artifacts():
    script = ROOT / "deploy" / "hd" / "deploy.sh"
    assert script.exists()
    content = script.read_text(encoding="utf-8")

    assert 'SKIP_MINIAPP_BUILD="${SKIP_MINIAPP_BUILD:-0}"' in content
    assert 'VITE_API_BASE="https://${DOMAIN}" npm run build:mp-weixin' in content
    assert 'grep -R "127\\.0\\.0\\.1\\|localhost\\|/fh/api\\|/fh/" -n dist/build/mp-weixin' in content
    assert "dist/build/mp-weixin src" not in content
    assert 'dist/build/mp-weixin/app.js' in content
