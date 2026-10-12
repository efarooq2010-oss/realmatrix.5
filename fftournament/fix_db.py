import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
print(f"Connecting to database at {db_path}...")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Check if 'diamonds' column exists in 'tournament_userprofile'
cursor.execute("PRAGMA table_info(tournament_userprofile);")
columns = [row[1] for row in cursor.fetchall()]

if 'diamonds' not in columns:
    print("Adding 'diamonds' column to 'tournament_userprofile'...")
    cursor.execute("ALTER TABLE tournament_userprofile ADD COLUMN diamonds decimal(12, 2) NOT NULL DEFAULT 100.00;")
    print("Column 'diamonds' added successfully!")
else:
    print("'diamonds' column already exists in 'tournament_userprofile'.")

# 2. Check if 'tournament_wallettransaction' table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tournament_wallettransaction';")
table_exists = cursor.fetchone()

if not table_exists:
    print("Creating 'tournament_wallettransaction' table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS "tournament_wallettransaction" (
            "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
            "transaction_type" varchar(20) NOT NULL,
            "amount_diamonds" decimal(12, 2) NOT NULL,
            "amount_euros" decimal(12, 2) NOT NULL,
            "description" varchar(255) NOT NULL,
            "timestamp" datetime NOT NULL,
            "status" varchar(20) NOT NULL,
            "user_id" bigint NOT NULL REFERENCES "tournament_userprofile" ("id") DEFERRABLE INITIALLY DEFERRED
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS 'tournament_wallettransaction_user_id_idx' ON 'tournament_wallettransaction' ('user_id');")
    print("Table 'tournament_wallettransaction' created successfully!")
else:
    print("'tournament_wallettransaction' table already exists.")

# 3. Record migration 0008 in django_migrations table if not present
cursor.execute("SELECT id FROM django_migrations WHERE app='tournament' AND name='0008_userprofile_diamonds_wallettransaction';")
migration_recorded = cursor.fetchone()

if not migration_recorded:
    from datetime import datetime
    cursor.execute(
        "INSERT INTO django_migrations (app, name, applied) VALUES (?, ?, ?);",
        ('tournament', '0008_userprofile_diamonds_wallettransaction', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    )
    print("Recorded migration '0008_userprofile_diamonds_wallettransaction' in django_migrations.")

conn.commit()
conn.close()
print("Database schema fix completed successfully!")
