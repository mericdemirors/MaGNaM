#!/bin/bash

set -euo pipefail

# ============================================================
# MaGNaM Security / Version Pre-Deployment Check
# ============================================================
#
# Purpose:
#   Check the current production environment before deployment
#   and generate an LLM-ready security/update review report.
#
# This script DOES NOT upgrade or install packages.
#
# ============================================================

APP_ROOT="/var/www/magnam/repository/magnam"
VENV="/var/www/magnam/venv"
FRONTEND="$APP_ROOT/frontend"
REQUIREMENTS="$APP_ROOT/requirements.txt"

export DJANGO_SETTINGS_MODULE="magnam.settings.production"
export DJANGO_ENV_FILE="/etc/magnam/.env.production"

cd "$APP_ROOT"

echo "Collecting production environment information..."

# ============================================================
# Helper
# ============================================================

get_version() {
    "$@" 2>/dev/null || echo "Unavailable"
}

# ============================================================
# Refresh APT metadata
# Does NOT install or upgrade anything.
# ============================================================

echo "Refreshing APT package metadata..."
sudo apt-get update -qq

# ============================================================
# OS
# ============================================================

UBUNTU_VERSION=$(
    . /etc/os-release
    echo "$PRETTY_NAME"
)

KERNEL_VERSION=$(uname -r)

# ============================================================
# Runtime
# ============================================================

PYTHON_VERSION=$(
    get_version "$VENV/bin/python" --version
)

PIP_VERSION=$(
    get_version "$VENV/bin/pip" --version
)

NODE_VERSION=$(
    get_version node --version
)

NPM_VERSION=$(
    get_version npm --version
)

GIT_VERSION=$(
    get_version git --version
)

# ============================================================
# Django
# ============================================================

DJANGO_VERSION=$(
    "$VENV/bin/python" -c \
        "import django; print(django.get_version())" \
        2>/dev/null \
        || echo "Unavailable"
)

# ============================================================
# PostgreSQL
# ============================================================

POSTGRES_CLIENT_VERSION=$(
    sudo -u postgres psql --version 2>/dev/null \
    || echo "Unavailable"
)

POSTGRES_SERVER_VERSION=$(
    sudo -u postgres psql -tAc "SELECT version();" 2>/dev/null \
    || echo "Unavailable"
)

POSTGRES_READY=$(
    sudo -u postgres pg_isready 2>/dev/null \
    || echo "Unavailable"
)

# ============================================================
# Redis
# ============================================================

REDIS_SERVER_VERSION=$(
    redis-server --version 2>/dev/null \
    || echo "Unavailable"
)

REDIS_RUNNING_VERSION=$(
    redis-cli INFO server 2>/dev/null \
    | grep '^redis_version:' \
    | cut -d: -f2 \
    | tr -d '\r' \
    || echo "Unavailable"
)

REDIS_PING=$(
    redis-cli ping 2>/dev/null \
    || echo "Unavailable"
)

# ============================================================
# Nginx / TLS / Git
# ============================================================

NGINX_VERSION=$(
    nginx -v 2>&1 \
    || echo "Unavailable"
)

OPENSSL_VERSION=$(
    openssl version 2>/dev/null \
    || echo "Unavailable"
)

CERTBOT_VERSION=$(
    certbot --version 2>&1 \
    || echo "Unavailable"
)

# ============================================================
# System dependencies used by MaGNaM
# ============================================================

POPPLER_VERSION=$(
    pdftoppm -v 2>&1 | head -n 1 \
    || echo "Unavailable"
)

GHOSTSCRIPT_VERSION=$(
    gs --version 2>/dev/null \
    || echo "Unavailable"
)

WEBP_VERSION=$(
    cwebp -version 2>&1 | head -n 1 \
    || echo "Unavailable"
)

# ============================================================
# Important APT package versions
# ============================================================

APT_PACKAGE_VERSIONS=$(
    dpkg-query -W -f='${Package}\t${Version}\n' 2>/dev/null \
    | grep -E \
      '^(nginx|openssl|ghostscript|poppler-utils|webp|postgresql|postgresql-[0-9]+|redis-server|nodejs|npm|certbot|python3-certbot-nginx)' \
    || echo "Unavailable"
)

# ============================================================
# Available APT updates
# ============================================================

APT_UPDATES=$(
    apt list --upgradable 2>/dev/null \
    | tail -n +2 \
    || echo "Unavailable"
)

# ============================================================
# Python dependency information
# ============================================================

PYTHON_PACKAGES=$(
    "$VENV/bin/pip" freeze 2>/dev/null \
    || echo "Unavailable"
)

PYTHON_CHECK=$(
    "$VENV/bin/pip" check 2>&1 \
    || true
)

# Important Python packages explicitly highlighted
IMPORTANT_PYTHON_PACKAGES=$(
    "$VENV/bin/pip" list --format=freeze 2>/dev/null \
    | grep -Ei \
      '^(Django|asgiref|channels|daphne|celery|redis|channels-redis|psycopg|PyMuPDF|Pillow|opencv-contrib-python|numpy|pandas|django-storages|boto3|sentry-sdk|moviepy|requests|urllib3|reportlab|pdfminer\.six|pypdf|django-cors-headers|djangorestframework|django-crontab|django-webpack-loader|whitenoise)=' \
    || true
)

# ============================================================
# Frontend dependency information
# ============================================================

if [[ -d "$FRONTEND" ]]; then

    NPM_PACKAGES=$(
        cd "$FRONTEND"
        npm list --depth=0 2>&1 \
        || true
    )

    NPM_AUDIT=$(
        cd "$FRONTEND"
        npm audit --omit=dev 2>&1 \
        || true
    )

    NPM_OUTDATED=$(
        cd "$FRONTEND"
        npm outdated 2>&1 \
        || true
    )

else
    NPM_PACKAGES="Frontend directory not found."
    NPM_AUDIT="Frontend directory not found."
    NPM_OUTDATED="Frontend directory not found."
fi

# ============================================================
# requirements.txt
# ============================================================

if [[ -f "$REQUIREMENTS" ]]; then
    DECLARED_REQUIREMENTS=$(cat "$REQUIREMENTS")
else
    DECLARED_REQUIREMENTS="requirements.txt not found."
fi

# ============================================================
# Production Django checks
# ============================================================

DJANGO_DEPLOY_CHECK=$(
    sudo -u magnam bash -c "
        cd '$APP_ROOT'
        DJANGO_SETTINGS_MODULE=magnam.settings.production \
        DJANGO_ENV_FILE='$DJANGO_ENV_FILE' \
        '$VENV/bin/python' manage.py check --deploy
    " 2>&1 || true
)

# ============================================================
# Production service status
# ============================================================

SERVICE_STATUS=$(
    sudo systemctl is-active \
        postgresql \
        redis-server \
        magnam-daphne \
        magnam-celery \
        nginx \
        magnam-backup.timer \
        2>&1 || true
)

# ============================================================
# Disk / memory
# ============================================================

MEMORY_STATUS=$(free -h)
DISK_STATUS=$(df -h /)

# ============================================================
# Generate final LLM-ready report
# ============================================================

cat <<EOF

============================================================
MaGNaM SECURITY / UPDATE REVIEW
============================================================

I have a project which uses the following platforms, services, and package versions.

Please review these against current official documentation, security advisories, CVEs, support policies, and release information.

Tell me whether these are appropriate for production use from a security and maintenance perspective.

Do NOT recommend upgrading something merely because a newer version exists. Consider security, support status, compatibility, and production stability.

============================================================
OPERATING SYSTEM
============================================================

Ubuntu:
$UBUNTU_VERSION

Kernel:
$KERNEL_VERSION

============================================================
PYTHON / APPLICATION RUNTIME
============================================================

Python:
$PYTHON_VERSION

pip:
$PIP_VERSION

Django:
$DJANGO_VERSION

Node.js:
$NODE_VERSION

npm:
$NPM_VERSION

Git:
$GIT_VERSION

============================================================
DATABASE / INFRASTRUCTURE
============================================================

PostgreSQL client:
$POSTGRES_CLIENT_VERSION

PostgreSQL server:
$POSTGRES_SERVER_VERSION

PostgreSQL readiness:
$POSTGRES_READY

Redis server package:
$REDIS_SERVER_VERSION

Redis running version:
$REDIS_RUNNING_VERSION

Redis ping:
$REDIS_PING

Nginx:
$NGINX_VERSION

OpenSSL:
$OPENSSL_VERSION

Certbot:
$CERTBOT_VERSION

============================================================
SYSTEM DEPENDENCIES
============================================================

Poppler:
$POPPLER_VERSION

Ghostscript:
$GHOSTSCRIPT_VERSION

WebP:
$WEBP_VERSION

============================================================
IMPORTANT PYTHON DEPENDENCIES
============================================================

$IMPORTANT_PYTHON_PACKAGES

============================================================
ALL INSTALLED PYTHON DEPENDENCIES
============================================================

$PYTHON_PACKAGES

============================================================
PYTHON DEPENDENCY CONSISTENCY CHECK
============================================================

$PYTHON_CHECK

============================================================
DECLARED requirements.txt
============================================================

$DECLARED_REQUIREMENTS

============================================================
NPM TOP-LEVEL DEPENDENCIES
============================================================

$NPM_PACKAGES

============================================================
NPM SECURITY AUDIT
============================================================

$NPM_AUDIT

============================================================
NPM OUTDATED PACKAGES
============================================================

$NPM_OUTDATED

============================================================
INSTALLED IMPORTANT APT PACKAGES
============================================================

$APT_PACKAGE_VERSIONS

============================================================
AVAILABLE UBUNTU / APT UPDATES
============================================================

$APT_UPDATES

============================================================
DJANGO PRODUCTION SECURITY CHECK
============================================================

$DJANGO_DEPLOY_CHECK

============================================================
PRODUCTION SERVICE STATUS
============================================================

$SERVICE_STATUS

============================================================
SERVER RESOURCES
============================================================

$MEMORY_STATUS

$DISK_STATUS

============================================================
UPDATE POLICY
============================================================

Ubuntu/system packages:
- Security updates promptly.
- Normal updates periodically.
- Verify/restart services after updates.

Python dependencies:
- Update in development first.
- Test before production.
- Security vulnerabilities get priority.

Django:
- Security releases promptly.
- Bugfix releases periodically.
- Major upgrades planned and tested separately.

npm dependencies:
- Update/test in development.
- Rebuild frontend before production deployment.
- Prioritize security updates.

PostgreSQL & Redis:
- Security/minor updates regularly.
- Major versions require planned upgrades.
- Verify backups before major changes.

Nginx / other system dependencies:
- Keep security-sensitive packages updated, especially OpenSSL, Nginx, Ghostscript, Poppler, etc.

Standard production process:

Review
→ Backup
→ Update in development
→ Test
→ Deploy
→ Verify services
→ Check logs/Sentry

============================================================
SECURITY REVIEW REQUEST
============================================================

Please provide an actionable production-readiness report.

For each package or platform requiring attention, classify it as:

CRITICAL
HIGH
MEDIUM
LOW
SAFE / NO ACTION

Specifically check:

1. Known CVEs/security vulnerabilities.
2. End-of-life status.
3. End-of-security-support status.
4. Available security updates.
5. Recommended stable production versions.
6. Whether an upgrade is security-critical or merely routine.
7. Whether an upgrade is a major-version change.
8. Whether a major upgrade may introduce compatibility risks.
9. Important security advisories affecting this stack.
10. Python dependency vulnerabilities.
11. npm dependency vulnerabilities.
12. Ubuntu/system package security updates.
13. Any concerning version constraints in requirements.txt.
14. Any obvious mismatch between installed versions and declared requirements.

Use current official sources wherever possible.

Do not assume the newest version is automatically the correct production version.

============================================================
END OF REPORT
============================================================

EOF