#!/bin/bash

set -euo pipefail

# ============================================================
# MaGNaM Production Deployment Script
# ============================================================

read -r -p "Did you check the security update policy? (yes/no): " SECURITY_POLICY_CHECKED

if [[ "${SECURITY_POLICY_CHECKED,,}" != "yes" ]]; then
    echo "Deployment cancelled. Check the security update policy first."
    exit 1
fi

read -r -p "Is Terms of Service and Privacy policy up to date after new changes? (yes/no): " TOS_AND_PP_CHECKED

if [[ "${TOS_AND_PP_CHECKED,,}" != "yes" ]]; then
    echo "Deployment cancelled. Update the Terms of Service and Privacy Policy first."
    exit 1
fi

APP_ROOT="/var/www/magnam/repository/magnam"
VENV="/var/www/magnam/venv"
DJANGO_SETTINGS_MODULE="magnam.settings.production"
DJANGO_ENV_FILE="/etc/magnam/.env.production"

export DJANGO_SETTINGS_MODULE
export DJANGO_ENV_FILE

sudo echo
echo "============================================================"
echo " MaGNaM Production Deployment"
echo "============================================================"
echo

cd "$APP_ROOT"

# ============================================================
# 1. Python dependencies
# ============================================================

echo "==> Installing Python dependencies..."

source "$VENV/bin/activate"

pip install -r requirements.txt --quiet

echo "✓ Python dependencies installed"
echo


# ============================================================
# 2. Frontend dependencies
# ============================================================

echo "==> Installing frontend dependencies..."

cd "$APP_ROOT/frontend"

npm ci

echo "✓ Frontend dependencies installed"
echo


# ============================================================
# 3. Build frontend
# ============================================================

echo "==> Building frontend..."

npm run build

echo "✓ Frontend build completed"
echo


# ============================================================
# 4. Verify frontend build
# ============================================================

echo "==> Verifying frontend build..."

test -f "$APP_ROOT/frontend/static/frontend/webpack-stats.json"
echo "✓ webpack-stats.json exists"

test -n "$(find "$APP_ROOT/frontend/static/frontend" \
    -maxdepth 1 \
    -type f \
    -name 'main.*.js' \
    -print -quit)"
echo "✓ main bundle exists"

test -n "$(find "$APP_ROOT/frontend/static/frontend" \
    -maxdepth 1 \
    -type f \
    -name 'runtime.*.js' \
    -print -quit)"
echo "✓ runtime bundle exists"

echo


# ============================================================
# 5. Django production checks
# ============================================================

echo "==> Running Django production checks..."

cd "$APP_ROOT"

"$VENV/bin/python" manage.py check --deploy

echo "✓ Django production checks passed"
echo


# ============================================================
# 6. Database migrations
# ============================================================

echo "==> Applying database migrations..."

"$VENV/bin/python" manage.py migrate --noinput

echo "✓ Database migrations applied"
echo


# ============================================================
# 7. Collect static files
# ============================================================

echo "==> Collecting static files..."

"$VENV/bin/python" manage.py collectstatic --noinput

echo "✓ Static files collected"
echo


# ============================================================
# 8. Reload services
# ============================================================

echo "==> Reloading production services..."

sudo systemctl daemon-reload

sudo systemctl restart magnam-daphne
sudo systemctl restart magnam-celery

echo "✓ Daphne restarted"
echo "✓ Celery restarted"
echo


# ============================================================
# 9. Validate Nginx and reload
# ============================================================

echo "==> Checking Nginx configuration..."

sudo nginx -t

sudo systemctl reload nginx

echo "✓ Nginx configuration valid"
echo "✓ Nginx reloaded"
echo


# ============================================================
# 10. Check services
# ============================================================

echo "==> Checking production services..."

sudo systemctl is-active \
    postgresql \
    redis-server \
    magnam-daphne \
    magnam-celery \
    nginx \
    magnam-backup.timer

echo "✓ All required services are active"
echo


# ============================================================
# 11. Check backups
# ============================================================

echo "==> Checking latest backups..."

sudo ls -lt /var/lib/magnam/backups/

echo


# ============================================================
# 12. Check website
# ============================================================

echo "==> Checking website..."

for i in {1..10}; do
    if curl -i --fail https://studiomagnam.com/ping/ >/dev/null 2>&1; then
        echo "✓ Website health check passed"
        break
    fi

    if [[ "$i" -eq 10 ]]; then
        echo "✗ Website did not respond with 200 OK after 10 attempts"
        curl -i --fail https://studiomagnam.com/ping/
        exit 1
    fi

    echo "  Website not ready yet, waiting..."
    sleep 2
done

echo


# ============================================================
# 13. Check frontend bundles
# ============================================================

echo "==> Checking frontend bundles..."

curl -s --fail https://studiomagnam.com/ \
    | grep -E 'frontend/.*(js|mjs)'

echo
echo "✓ Frontend bundles are being served"
echo


# ============================================================
# 14. Check disk and RAM
# ============================================================

echo "==> Checking RAM..."

free -h

echo
echo "==> Checking disk..."

df -h /

echo


# ============================================================
# 15. Check PostgreSQL
# ============================================================

echo "==> Checking PostgreSQL..."

sudo -u postgres pg_isready

sudo -u postgres psql \
    -d magnam_postgres_db \
    -c "SELECT 1;"

sudo -u postgres psql \
    -d magnam_postgres_db \
    -c "SELECT count(*) AS active_connections FROM pg_stat_activity;"

echo "✓ PostgreSQL checks passed"
echo


# ============================================================
# 16. Check Redis
# ============================================================

echo "==> Checking Redis..."

redis-cli ping

redis-cli INFO server | grep redis_version

echo "✓ Redis checks passed"
echo


# ============================================================
# 17. Check Celery
# ============================================================

for i in {1..10}; do
    if "$VENV/bin/celery" \
        -A magnam \
        inspect ping >/dev/null 2>&1; then

        echo "✓ Celery worker responded"
        break
    fi

    if [[ "$i" -eq 10 ]]; then
        echo "✗ Celery worker did not respond after 10 attempts"
        exit 1
    fi

    echo "  Celery not ready yet, waiting..."
    sleep 2
done

# ============================================================
# 18. Django cron jobs
# ============================================================

echo "==> Updating Django cron jobs..."

"$VENV/bin/python" manage.py crontab remove
"$VENV/bin/python" manage.py crontab add

echo "✓ Django cron jobs updated"
echo

# ============================================================
# DEPLOYMENT COMPLETE
# ============================================================

echo
echo "============================================================"
echo " MaGNaM deployment completed successfully"
echo "============================================================"
echo