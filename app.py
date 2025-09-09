from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import pickle
import os
import re
import numpy as np
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Load trained model
model_path = "C:/disease_prediction_system/models/model.pkl"
if os.path.exists(model_path):
    with open(model_path, "rb") as model_file:
        model = pickle.load(model_file)
else:
    model = None
    print("⚠️ Model file not found! Train the model first.")

# Database setup
DATABASE = "C:/disease_prediction_system/disease_prediction.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Ensure database and users table exist
def create_users_table():
    conn = get_db_connection()
    cursor = conn.cursor()
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
        )
    """)
    conn.commit()
    conn.close()

# Run table creation
create_users_table()

# ========================== USER AUTHENTICATION ==========================

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    conn = None  # Ensure conn is always initialized

    if request.method == "POST":
        try:
            username = request.form["username"].strip()
            password = request.form["password"].strip()
            name = request.form["name"].strip()
            age = request.form["age"].strip()
            sex = request.form["sex"].strip()
            father_name = request.form["father_name"].strip()
            mother_name = request.form["mother_name"].strip()
            address = request.form["address"].strip()
            contact = request.form["contact"].strip()

            if not all([username, password, name, age, sex, father_name, mother_name, address, contact]):
                flash("❌ All fields are required!", "danger")
                return render_template("register.html")

# Validate username (at least 3 characters, only letters and numbers allowed)
            if not re.match(r"^[A-Za-z0-9]{3,}$", username):
                flash("❌ Username must be at least 3 characters long and contain only letters and numbers.", "danger")
                return render_template("register.html")

# Validate name (only alphabets, at least 3 characters)
            if not re.match(r"^[A-Za-z]{3,}$", name):
                flash("❌ Name must contain only letters and be at least 3 characters long.", "danger")
                return render_template("register.html")

# Validate sex selection
            if sex not in ["Male", "Female", "Other"]:
                flash("❌ Invalid selection for sex!", "danger")
                return render_template("register.html")

# Validate password (minimum 4 characters, either all numbers or all letters)
            if len(password) < 4 or not password.isalnum():
                flash("❌ Password must be at least 4 characters long and contain only letters or numbers.", "danger")
                return render_template("register.html")

# Validate father's and mother's names (only alphabets, at least 3 characters)
            name_pattern = r"^[A-Za-z]{3,}$"
            if not re.match(name_pattern, father_name):
                flash("❌ Father's name must contain only letters and be at least 3 characters long.", "danger")
                return render_template("register.html")

            if not re.match(name_pattern, mother_name):
                flash("❌ Mother's name must contain only letters and be at least 3 characters long.", "danger")
                return render_template("register.html")

# Validate age (must be a number between 1 and 120)
            if not age.isdigit() or int(age) < 1 or int(age) > 120:
                flash("❌ Age must be a valid number between 1 and 120.", "danger")
                return render_template("register.html")

# Validate address (minimum 5 characters)
            if len(address) < 5:
                flash("❌ Address must be at least 5 characters long.", "danger")
                return render_template("register.html")

# Validate contact number (only digits, 10-15 characters)
            if not re.match(r"^\d{10}$", contact):
                flash("❌ Contact number must be between 10 digits long.", "danger")
                return render_template("register.html")

            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if username already exists
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                flash("❌ Username already taken!", "danger")
                return render_template("register.html")

            # Hash the password and store the user
            hashed_password = generate_password_hash(password)
            cursor.execute(
                "INSERT INTO users (username, password, name, age, sex, father_name, mother_name, address, contact) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (username, hashed_password, name, age, sex, father_name, mother_name, address, contact),
            )
            conn.commit()
            flash("✅ Registration successful! Please log in.", "success")
            return redirect(url_for("login"))

        except sqlite3.OperationalError as e:
            flash(f"❌ Database error: {e}", "danger")

        finally:
            if conn:
                conn.close()

    return render_template("register.html")



@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        if not username or not password:
            flash("❌ Username and password are required!", "danger")
            return redirect(url_for("login"))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash("✅ Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("❌ Incorrect username or password!", "danger")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("👋 You have been logged out.", "info")
    return redirect(url_for("login"))

# ========================== USER DASHBOARD ==========================

@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        flash("⚠️ Please log in first!", "warning")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch user details
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()

    # Fetch prediction history
    cursor.execute("SELECT * FROM predictions WHERE user_id = ? ORDER BY prediction_date DESC", (user_id,))
    history = cursor.fetchall()

    conn.close()
    
    return render_template("user_details.html", user=user, history=history)


@app.route("/update_user", methods=["GET", "POST"])
def update_user():
    if "username" not in session:
        flash("⚠️ Please log in first!", "warning")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()

    if request.method == "POST":
        try:
            name = request.form["name"].strip()
            age = request.form["age"].strip()
            sex = request.form["sex"].strip()
            father_name = request.form["father_name"].strip()
            mother_name = request.form["mother_name"].strip()
            address = request.form["address"].strip()
            contact = request.form["contact"].strip()

            if not all([name, age, sex, father_name, mother_name, address, contact]):
                flash("❌ All fields are required!", "danger")
                return redirect(url_for("update_user"))

            cursor.execute("""
                UPDATE users SET name=?, age=?, sex=?, father_name=?, mother_name=?, address=?, contact=?
                WHERE id=?
            """, (name, age, sex, father_name, mother_name, address, contact, user_id))

            conn.commit()
            flash("✅ Profile updated successfully!", "success")
            return redirect(url_for("dashboard"))

        except sqlite3.OperationalError as e:
            flash(f"❌ Database error: {e}", "danger")

    conn.close()
    return render_template("update_user.html", user=user)


# ========================== DISEASE PREDICTION ==========================

@app.route("/prediction_page", methods=["GET", "POST"])
def prediction_page():
    if "username" not in session:
        flash("⚠️ Please log in first!", "warning")
        return redirect(url_for("login"))

    if request.method == "POST":
        try:
            required_fields = ["blood_sugar", "cholesterol", "liver_enzyme", "kidney_function", "thyroid_level"]
            input_data = []

            for field in required_fields:
                try:
                    value = float(request.form[field].strip())
                    if value < 0:
                        flash(f"❌ {field.replace('_', ' ').capitalize()} cannot be negative!", "danger")
                        return redirect(url_for("predict"))
                    input_data.append(value)
                except ValueError:
                    flash(f"❌ {field.replace('_', ' ').capitalize()} must be a valid number!", "danger")
                    return redirect(url_for("predict"))

            input_data = np.array([input_data])

            if not model:
                flash("❌ Prediction model not found!", "danger")
                return redirect(url_for("dashboard"))

            prediction = model.predict(input_data)[0]
            disease_labels = ["Diabetes", "Heart Disease", "Liver Disease", "Kidney Disease", "Thyroid Disease"]
            detected_diseases = [disease_labels[i] for i in range(len(prediction)) if prediction[i] == 1]
            detected_diseases_str = ", ".join(detected_diseases) if detected_diseases else "No disease detected"

            # Save prediction to database
            user_id = session["user_id"]
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO predictions (user_id, blood_sugar, cholesterol, liver_enzyme, kidney_function, thyroid_level, detected_diseases)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, *input_data[0], detected_diseases_str))
            conn.commit()
            conn.close()

            # Health tips
            health_tips = {
                "Diabetes": "🩸 Maintain a healthy diet, exercise regularly, and monitor blood sugar levels.",
                "Heart Disease": "❤️ Eat heart-healthy foods, avoid smoking, and manage stress.",
                "Liver Disease": "🍎 Reduce alcohol intake, eat a balanced diet, and stay hydrated.",
                "Kidney Disease": "💧 Limit salt intake, drink plenty of water, and manage blood pressure.",
                "Thyroid Disease": "🦋 Ensure adequate iodine intake and get regular thyroid check-ups."
            }
            tips = [health_tips[d] for d in detected_diseases] if detected_diseases else ["✅ You are healthy! No disease detected."]

            return render_template("result.html", detected_diseases=detected_diseases, tips=tips)

        except Exception as e:
            flash(f"⚠️ Error in prediction: {str(e)}", "danger")

    return render_template("prediction_page.html")


@app.route("/prediction_history")
def prediction_history():
    if "username" not in session:
        flash("⚠️ Please log in first!", "warning")
        return redirect(url_for("login"))

    conn = sqlite3.connect("C:/disease_prediction_system/disease_prediction.db")
    cursor = conn.cursor()
 
    cursor.execute("SELECT * FROM predictions WHERE user_id = ? ORDER BY prediction_date DESC", (user_id,))
    history = cursor.fetchall()
    conn.close()

    return render_template("prediction_history.html", history=history)

if __name__ == "__main__":
    app.run(debug=True)
