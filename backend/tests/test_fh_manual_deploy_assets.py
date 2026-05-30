from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_fh_manual_deploy_script_contains_git_pull_and_isolated_paths():
    script = ROOT / "deploy" / "fh" / "manual-deploy.sh"
    assert script.exists()
    content = script.read_text(encoding="utf-8")

    assert "APP_DIR=\"${APP_DIR:-/www/dk_project/wwwroot/fh}\"" in content
    assert "REPO_URL=\"${REPO_URL:-https://github.com/reynold2/hd.git}\"" in content
    assert "git_pull_latest" in content
    assert "git pull --ff-only" in content
    assert "VITE_API_BASE=\"/fh\"" in content
    assert "npm run build -- --base=/fh/admin/" in content
    assert "npm run build:h5 -- --base=/fh/customer/" in content
    assert "SERVICE_NAME=\"${SERVICE_NAME:-fh-queue.service}\"" in content
    assert "BACKEND_PORT=\"${BACKEND_PORT:-8020}\"" in content
    assert "/www/dk_project/wwwroot/yuyue-saas" not in content
    assert "yuyue-saas.service" not in content
