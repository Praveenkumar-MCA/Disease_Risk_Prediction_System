import sqlite3

# Define database path
DATABASE = "C:/disease_prediction_system/disease_prediction.db"

# Connect to SQLite
conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

# Create 'users' table (already exists in your setup)
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    sex TEXT CHECK (sex IN ('Male', 'Female', 'Other')) NOT NULL,
    father_name TEXT NOT NULL,
    mother_name TEXT NOT NULL,
    address TEXT NOT NULL,
    contact TEXT NOT NULL
);
""")

# Create 'predictions' table to store prediction history
cursor.execute("""
CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    blood_sugar REAL NOT NULL,
    cholesterol REAL NOT NULL,
    liver_enzyme REAL NOT NULL,
    kidney_function REAL NOT NULL,
    thyroid_level REAL NOT NULL,
    detected_diseases TEXT NOT NULL,
    prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
""")

# Commit and close
conn.commit()
conn.close()

print("Database setup complete! Tables created.")
