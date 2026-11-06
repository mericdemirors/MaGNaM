# COMMANDS TO START THE DEVELOPMENT MACHINE SERVER

# 1 start PDF parsing service
celery -A magnam -b 'redis://localhost:6379/0' purge -f; systemd-run --scope -p MemoryMax=2G -p CPUQuota=200% -p IOWeight=10 nice -n 10 celery -A magnam worker --loglevel=debug --concurrency=2
# 2 resets the development server (also prepares the next one with migrations and populations)
./refresh_database.sh
# 3 prepares to serve the frontned
cd frontend; npm run dev
# 4 starts serving the django server
DJANGO_SETTINGS_MODULE=magnam.settings.development DJANGO_ENV_FILE=.env.development daphne -b 127.0.0.1 -p 8000 magnam.asgi:application




# COMMANDS TO CHECK IF DEVELOPMENT READY TO PUSH

# check migrations
python manage.py makemigrations --check --dry-run
# django backend unittests:
python manage.py test --parallel 8 
python manage.py test tests.test_files
# also add frontend unittests:
# TODO
# verify npm dependencies
cd frontend; npm ci
# Run the production frontend build.
cd frontend; npm run build
# Verify generated frontend/static files.
cd frontend; test -f static/frontend/webpack-stats.json && echo "✓ webpack-stats.json exists"
cd frontend; test -n "$(find static/frontend -maxdepth 1 -type f -name 'main.*.js' -print -quit)" && echo "✓ main bundle exists"
cd frontend; test -n "$(find static/frontend -maxdepth 1 -type f -name 'runtime.*.js' -print -quit)" && echo "✓ runtime bundle exists"




# COMMANDS TO PREPARE THE PRODUCTION MACHINE SERVER

# install dependencies
source /var/www/magnam/venv/bin/activate
export DJANGO_SETTINGS_MODULE=magnam.settings.production
export DJANGO_ENV_FILE=/etc/magnam/.env.production
cd magnam; pip install -r requirements.txt --quiet
cd frontend; npm ci
# build frontend
cd frontend; npm run build
# verify files
cd frontend; test -f static/frontend/webpack-stats.json && echo "✓ webpack-stats.json exists"
cd frontend; test -n "$(find static/frontend -maxdepth 1 -type f -name 'main.*.js' -print -quit)" && echo "✓ main bundle exists"
cd frontend; test -n "$(find static/frontend -maxdepth 1 -type f -name 'runtime.*.js' -print -quit)" && echo "✓ runtime bundle exists"
# check django production state
python manage.py check --deploy
# apply database migrations
python manage.py migrate --noinput
# collect statics (dont use --clear)
python manage.py collectstatic --noinput




# COMMANDS TO START SERVING THE NEW VERSION

# restart and reload services
sudo systemctl daemon-reload
sudo systemctl restart magnam-daphne
sudo systemctl restart magnam-celery
# reload nginx if config is changed
sudo nginx -t && sudo systemctl reload nginx
# check if services are running
sudo systemctl is-active postgresql redis-server magnam-daphne magnam-celery nginx magnam-backup.timer
# check the last backups
sudo ls -lt /var/lib/magnam/backups/
# check if website is up
curl -i https://studiomagnam.com/ping/
# check if nginx is serving the bundles
curl -s https://studiomagnam.com/ | grep -E 'frontend/.*(js|mjs)'
# check DISK and RAM
free -h
df -h /
# check postgres
sudo -u postgres pg_isready
sudo -u postgres psql -d magnam_postgres_db -c "SELECT 1;"
sudo -u postgres psql -d magnam_postgres_db -c \
"SELECT count(*) AS active_connections FROM pg_stat_activity;"
# check redis
redis-cli ping
redis-cli INFO server | grep redis_version
sudo -u magnam bash -c '
cd /var/www/magnam/repository/magnam
DJANGO_SETTINGS_MODULE=magnam.settings.production \
DJANGO_ENV_FILE=/etc/magnam/.env.production \
../../venv/bin/celery -A magnam inspect ping'



# COMMANDS TO DO POSTGRES BACKUP ACTIONS

# how to manually backup the current database:
sudo -u magnam-backup /usr/local/sbin/magnam-backup
# how to manually check if backup file is corrupt or not
sudo -u magnam-backup pg_restore \
    --list \
    /var/lib/magnam/backups/PUT_NEWEST_BACKUP_FILENAME_HERE.dump | head -20




# COMMANDS TO RESTORE A BACKED UP DATABASE STATE
# ! DELETES THE CURRENT DATABASE STATE

# how to manually check if backup file is corrupt or not
sudo -u magnam-backup pg_restore \
    --list \
    /var/lib/magnam/backups/PUT_BACKUP_FILENAME_HERE.dump | head -20
# Stop application services to prevent new database connections
sudo systemctl stop magnam-daphne magnam-celery
# Terminate remaining connections to the database
sudo -u postgres psql -c \
"SELECT pg_terminate_backend(pid)
 FROM pg_stat_activity
 WHERE datname = 'magnam_postgres_db'
   AND pid <> pg_backend_pid();"
# Delete the existing database
sudo -u postgres dropdb magnam_postgres_db
# Recreate the database with the correct owner
sudo -u postgres createdb \
    --owner=magnam_postgres_user \
    magnam_postgres_db
# Restore the selected backup
sudo -u magnam-backup env PGPASSFILE=/etc/magnam/backup/.pgpass \
    pg_restore \
    --host=127.0.0.1 \
    --port=5432 \
    --username=magnam_postgres_user \
    --dbname=magnam_postgres_db \
    /var/lib/magnam/backups/PUT_BACKUP_FILENAME_HERE.dump
# Verify restored database
sudo -u postgres psql -d magnam_postgres_db -c \
"SELECT count(*) AS tables FROM pg_tables WHERE schemaname = 'public';"
sudo -u postgres psql -d magnam_postgres_db -c \
"SELECT count(*) AS users FROM auth_user;"
# Verify Django can use the restored database
cd /var/www/magnam/repository/magnam
sudo -u magnam bash -c '
DJANGO_SETTINGS_MODULE=magnam.settings.production \
DJANGO_ENV_FILE=/etc/magnam/.env.production \
../../venv/bin/python manage.py check
'
# Start application services again
sudo systemctl start magnam-celery
sudo systemctl start magnam-daphne
# Verify services
sudo systemctl is-active postgresql redis-server magnam-daphne magnam-celery nginx