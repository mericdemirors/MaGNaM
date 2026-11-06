import os
import sys
from pathlib import Path
import shutil
import psycopg
from dotenv import load_dotenv

# 1. Resolve project root (directory containing utils/, manage.py, magnam/)
script_dir = Path(__file__).resolve().parent
base_path = script_dir.parent

# 2. Add project root to sys.path so Python can find 'magnam'
sys.path.insert(0, str(base_path))

# 3. Load environment variables before Django setup
env_path = base_path / ".env.development"
load_dotenv(dotenv_path=env_path)


# 4. User confirmation prompt
def confirm_cleanup():
    answer = input(
        "WARNING: This will reset the database, and remove media files. Continue? (y/N): "
    )
    if answer.lower() != "y":
        print("Cleanup cancelled.")
        exit(0)


confirm_cleanup()

# 5. Initialize Django
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "magnam.settings.development")
django.setup()

from django.conf import settings

# 4. Reset PostgreSQL Database
db_name = os.getenv("POSTGRES_DB")
db_user = os.getenv("POSTGRES_USER")
db_password = os.getenv("POSTGRES_PASSWORD")
db_host = os.getenv("POSTGRES_HOST", "127.0.0.1")
db_port = os.getenv("POSTGRES_PORT", "5432")

if db_name and db_user:
    try:
        conn = psycopg.connect(
            dbname="postgres",
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
            autocommit=True,
        )

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = %s
              AND pid <> pg_backend_pid();
            """,
            (db_name,),
        )

        cursor.execute(f'DROP DATABASE IF EXISTS "{db_name}";')
        print(f"dropped database '{db_name}'.")

        cursor.execute(f'CREATE DATABASE "{db_name}";')
        print(f"created fresh database '{db_name}'.")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Failed to reset PostgreSQL database '{db_name}': {e}")
else:
    print(
        f"Missing database environment variables "
        f"(POSTGRES_DB / POSTGRES_USER) from {env_path}."
    )


# 5. Clean media folders
MEDIA_ROOT = settings.MEDIA_ROOT
TEST_MEDIA_ROOT = settings.TEST_MEDIA_ROOT
LOG_DIR = settings.LOG_DIR

folders_to_clean = [
    settings.COMPETITIONS_MEDIA_FOLDERNAME,
    settings.NEWS_MEDIA_FOLDERNAME,
    settings.MANGAS_MEDIA_FOLDERNAME,
    settings.PORTFOLIOS_MEDIA_FOLDERNAME,
    settings.PROFILES_MEDIA_FOLDERNAME,
]


def clean_folder(folder_path: Path):
    if not folder_path.exists():
        print(f"Folder not found: {folder_path}")
        return
    for item in folder_path.iterdir():
        try:
            if item.is_file() or item.is_symlink():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
        except Exception as e:
            print(f"Failed to delete {item}: {e}")


for folder in folders_to_clean:
    clean_folder(MEDIA_ROOT / folder)
clean_folder(TEST_MEDIA_ROOT)
clean_folder(LOG_DIR)
print("Database cleanup completed.")
