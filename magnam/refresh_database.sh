#!/bin/bash

# Confirmation gate
read -p "WARNING: This will reset the database, delete migrations, clean media, and repopulate data. Continue? (y/N): " CONFIRM

if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
    echo "Operation cancelled."
    exit 0
fi

# Run from the directory containing manage.py (Django project root)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DATASET_DIR="${DATASET_DIR:-$SCRIPT_DIR/../dataset_population}"
cd "$SCRIPT_DIR" || exit 1

# DELETE THE OLD DATABASE
python3 manage.py flush --no-input
python3 utils/clean_up.py

# SET THE NEW ONE
python3 manage.py makemigrations
python3 manage.py migrate

# CREATE THE TAGS AND DUMMY USERS IF NEEDED
python3 manage.py populate_manga_tags
python3 manage.py populate_portfolio_tags
python3 manage.py populate_competition_tags
python3 manage.py populate_kanbantask_tags

# BELOW ARE COMMENTED, AND ONLY FOR LOCAL DEVELOPMENT, DONT POPULATE THE CLOUD R2 SERVER

python3 manage.py populate_dev_users

# # POPULATE THE DATABASE WITH DUMMY CONTENT IF NEEDED (set DATASET_DIR if files live elsewhere)
# # it is a command like this: python3 manage.py populate_batch_chapters "/absolute/path/to/the/file/../dataset_population/batch_chapters.xlsx"
python3 manage.py populate_batch_news "$DATASET_DIR/batch_news.xlsx"
python3 manage.py populate_batch_competitions "$DATASET_DIR/batch_competitions.xlsx"
python3 manage.py populate_batch_portfolios "$DATASET_DIR/batch_portfolios.xlsx"
python3 manage.py populate_batch_works "$DATASET_DIR/batch_works.xlsx"
python3 manage.py populate_batch_mangas "$DATASET_DIR/batch_mangas.xlsx"
python3 manage.py populate_batch_chapters "$DATASET_DIR/batch_chapters.xlsx"