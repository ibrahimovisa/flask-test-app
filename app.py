from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mail import Mail, Message
import random
import psycopg2
import os
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
import threading
import time
from datetime import datetime, timedelta
import logging

app = Flask(__name__)
app.secret_key = os.urandom(24)  # More secure secret key

logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Using Gmail SMTP server
app.config['MAIL_PORT'] = 587  # SMTP port for Gmail
app.config['MAIL_USE_TLS'] = True  # Use TLS encryption
app.config['MAIL_USERNAME'] = 'ibrahimovisa2004@gmail.com'  # Your Gmail address
app.config['MAIL_PASSWORD'] = 'olercodlueziexyi'  # Your Gmail app password
app.config['MAIL_DEFAULT_SENDER'] = 'ibrahimovisa2004@gmail.com'  # Default sender
mail = Mail(app)

# Database configuration
# Database connection function
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT", 5432)  # по умолчанию 5432
    )

# Function to send Email
def send_verification_email(email, verification_code):
    try:
        msg = Message('Account Verification', recipients=[email])
        msg.body = f'Your verification code is: {verification_code}'
        mail.send(msg)
        print(f"Verification email sent to {email}")
    except Exception as e:
        print(f"Error sending email: {e}")
        flash("Failed to send email. Please try again.")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        phone_number = request.form["phone_number"]
        birthday = request.form["birthday"]

        # Generate 6-digit verification code
        verification_code = random.randint(100000, 999999)
        session["verification_code"] = verification_code  # Store in session for verification
        session["email"] = email  # Store email
        session["name"] = name  # Store user name
        session["password"] = password  # Store password
        session["phone_number"] = phone_number  # Store phone number
        session["birthday"] = birthday  # Store birthday

        # Send verification email
        send_verification_email(email, verification_code)

        return redirect(url_for("verify_email"))
    return render_template("signup.html")

@app.route("/verify_email", methods=["GET", "POST"])
def verify_email():
    if request.method == "POST":
        user_code = request.form["verification_code"]
        if "verification_code" in session and str(user_code) == str(session["verification_code"]):
            # Save user to the database
            conn = get_db_connection()
            cur = conn.cursor()
            
            # Reset the sequence to the next available ID
            cur.execute("SELECT setval(pg_get_serial_sequence('users', 'id'), COALESCE((SELECT MAX(id) FROM users), 0) + 1, false)")
            
            # Then insert the new user
            cur.execute(
                "INSERT INTO users (name, email, password, phone_number, birthday, role) "
                "VALUES (%s, %s, %s, %s, %s, 'student')",
                (session["name"], session["email"], session["password"], 
                 session["phone_number"], session["birthday"])
            )
            conn.commit()
            cur.close()
            conn.close()

            flash("Account created successfully!")
            return redirect(url_for("login"))
        else:
            flash("Incorrect verification code. Try again.")
    return render_template("verify_email.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, email, role FROM users WHERE email = %s AND password = %s", (email, password))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            session["user_id"] = user[0]
            session["name"] = user[1]
            session["email"] = user[2]
            session["role"] = user[3]

            flash("Login successful!")

            if user[3] == "admin":
                return redirect(url_for("admin_dashboard"))
            elif user[3] == "teacher":
                return redirect(url_for("teacher_dashboard"))  # New route for teachers
            else:
                return redirect(url_for("user_dashboard"))

        else:
            flash("Invalid credentials. Please try again.")

    return render_template("login.html")

@app.route("/user_dashboard")
def user_dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    
    conn = get_db_connection()
    cur = conn.cursor()

    # Get all courses where user is enrolled and has a group (for My Courses)
    cur.execute("""
        SELECT DISTINCT c.id, c.name, c.description, c.image_url, g.group_name
        FROM courses c
        JOIN groups g ON c.id = g.course_id
        JOIN group_members gm ON g.id = gm.group_id
        WHERE gm.user_id = %s
        ORDER BY c.name
    """, (user_id,))
    enrolled_courses = cur.fetchall()

    # Get courses where user is enrolled but not in any group (for Waiting Courses)
    cur.execute("""
        SELECT c.id, c.name, c.description, c.image_url
        FROM courses c
        JOIN user_courses uc ON c.id = uc.course_id
        WHERE uc.user_id = %s
        AND NOT EXISTS (
            SELECT 1 FROM group_members gm
            JOIN groups g ON gm.group_id = g.id
            WHERE gm.user_id = %s AND g.course_id = c.id
        )
        ORDER BY c.name
    """, (user_id, user_id))
    waiting_courses = cur.fetchall()

    # Get all courses not enrolled in any way (for Available Courses)
    cur.execute("""
        SELECT c.id, c.name, c.description, c.image_url
        FROM courses c
        WHERE NOT EXISTS (
            SELECT 1 FROM user_courses uc WHERE uc.user_id = %s AND uc.course_id = c.id
        )
        AND NOT EXISTS (
            SELECT 1 FROM group_members gm
            JOIN groups g ON gm.group_id = g.id
            WHERE gm.user_id = %s AND g.course_id = c.id
        )
        ORDER BY c.name
    """, (user_id, user_id))
    available_courses = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("user_dashboard.html", 
                         enrolled_courses=enrolled_courses,
                         available_courses=available_courses,
                         waiting_courses=waiting_courses)




# =================================================================






# Helper function to get the maximum day for a course and group
def get_max_day(course_id, group_name):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT MAX(day) FROM attendance a
                JOIN groups g ON a.group_id = g.id
                WHERE g.course_id = %s AND g.group_name = %s
            """, (course_id, group_name))
            max_day = cur.fetchone()[0]
            return max_day if max_day else 0
    except Exception as e:
        app.logger.error(f"Error getting max day: {e}")
        return 0
    finally:
        conn.close()



@app.route("/admin_dashboard")
def admin_dashboard():
    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Get all users except current admin
            cur.execute("""
                SELECT id, name, email, role, created_at, phone_number, birthday 
                FROM users WHERE id != %s ORDER BY created_at DESC
            """, (session["user_id"],))
            users = cur.fetchall()

            # Get all courses
            cur.execute("SELECT id, name FROM courses ORDER BY name")
            courses = cur.fetchall()

            # Get all teachers for group creation
            cur.execute("SELECT id, name FROM users WHERE role = 'teacher' ORDER BY name")
            teachers = cur.fetchall()

            # Get students waiting for group creation - modified query
            # In the admin_dashboard route, modify the query to:
            cur.execute("""
                SELECT 
                    uc.user_id, 
                    u.name as user_name, 
                    u.email as user_email, 
                    c.name as course_name, 
                    TO_CHAR(uc.enrolled_at, 'DD-MM-YYYY') as enrolled_at_formatted,
                    u.phone_number
                FROM user_courses uc
                JOIN users u ON uc.user_id = u.id
                JOIN courses c ON uc.course_id = c.id
                LEFT JOIN group_members gm ON uc.user_id = gm.user_id AND 
                    EXISTS (
                        SELECT 1 FROM groups g 
                        WHERE g.id = gm.group_id AND g.course_id = uc.course_id
                    )
                WHERE gm.user_id IS NULL AND u.role = 'student'
                ORDER BY uc.enrolled_at DESC
            """)
            students_waiting = [dict((cur.description[i][0], value) for i, value in enumerate(row)) 
                              for row in cur.fetchall()]

        return render_template("admin_dashboard.html", 
                             users=users, 
                             courses=courses,
                             teachers=teachers,
                             students_waiting=students_waiting)
    except Exception as e:
        app.logger.error(f"Error in admin dashboard: {e}")
        flash("An error occurred while loading the dashboard", "error")
        return redirect(url_for("index"))
    finally:
        conn.close()

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("login"))

@app.route("/delete_user/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    if user_id == session["user_id"]:
        return jsonify({"error": "Cannot delete yourself"}), 400

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Get user role first
            cur.execute("SELECT role FROM users WHERE id = %s", (user_id,))
            result = cur.fetchone()
            if not result:
                return jsonify({"error": "User not found"}), 404
            role = result[0]

            # Delete all references to this user in other tables
            # 1. Delete from user_courses
            cur.execute("DELETE FROM user_courses WHERE user_id = %s", (user_id,))
            
            # 2. Delete attendance records
            cur.execute("DELETE FROM attendance WHERE user_id = %s", (user_id,))
            
            # 3. Delete from group_members and check for empty groups
            cur.execute("DELETE FROM group_members WHERE user_id = %s RETURNING group_id", (user_id,))
            deleted_groups = [row[0] for row in cur.fetchall()]
            
            # Delete any now-empty groups
            for group_id in deleted_groups:
                cur.execute("""
                    DELETE FROM groups WHERE id = %s AND NOT EXISTS (
                        SELECT 1 FROM group_members WHERE group_id = %s
                    )
                """, (group_id, group_id))
            
            # If teacher, delete their teacher_courses and groups
            if role == "teacher":
                # Get groups to delete attendance for them first
                cur.execute("SELECT id FROM groups WHERE teacher_id = %s", (user_id,))
                teacher_groups = [row[0] for row in cur.fetchall()]
                
                if teacher_groups:
                    # Delete attendance for these groups
                    cur.execute("DELETE FROM attendance WHERE group_id = ANY(%s)", (teacher_groups,))
                    # Delete group members
                    cur.execute("DELETE FROM group_members WHERE group_id = ANY(%s)", (teacher_groups,))
                    # Delete the groups
                    cur.execute("DELETE FROM groups WHERE id = ANY(%s)", (teacher_groups,))
                
                # Delete teacher_courses
                cur.execute("DELETE FROM teacher_courses WHERE teacher_id = %s", (user_id,))
            
            # Finally delete the user
            cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
            
            conn.commit()
            return jsonify({
                "success": True,
                "message": "User deleted successfully",
                "role": role,
                "group_deleted": len(deleted_groups) > 0
            })

    except Exception as e:
        if conn: conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()


@app.route("/enroll/<int:course_id>", methods=["POST"])
def enroll(course_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Check if already in a group for this course
        cur.execute("""
            SELECT 1 FROM group_members gm
            JOIN groups g ON gm.group_id = g.id
            WHERE gm.user_id = %s AND g.course_id = %s
        """, (user_id, course_id))
        
        if cur.fetchone():
            flash("You are already in a group for this course")
            return redirect(url_for("user_dashboard"))

        # Check if already enrolled but not in a group
        cur.execute("""
            SELECT 1 FROM user_courses 
            WHERE user_id = %s AND course_id = %s
        """, (user_id, course_id))
        
        if cur.fetchone():
            flash("You are already enrolled and waiting for group assignment")
            return redirect(url_for("user_dashboard"))

        # Enroll the user
        cur.execute("""
            INSERT INTO user_courses (user_id, course_id)
            VALUES (%s, %s)
        """, (user_id, course_id))
        conn.commit()
        flash("Successfully enrolled in the course!")

    except Exception as e:
        conn.rollback()
        flash("Error enrolling in course")
        app.logger.error(f"Error enrolling user {user_id} in course {course_id}: {e}")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("user_dashboard"))

@app.route("/course/<int:course_id>")
def course_page(course_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    
    conn = get_db_connection()
    cur = conn.cursor()

    # Verify user is enrolled
    cur.execute("""
        SELECT 1 FROM user_courses 
        WHERE user_id = %s AND course_id = %s
    """, (user_id, course_id))
    
    if not cur.fetchone():
        flash("You need to enroll in this course first")
        return redirect(url_for("user_dashboard"))

    # Get course details
    cur.execute("""
        SELECT name, description, image_url 
        FROM courses 
        WHERE id = %s
    """, (course_id,))
    course = cur.fetchone()

    # Get user progress
    cur.execute("""
        SELECT progress 
        FROM user_courses 
        WHERE user_id = %s AND course_id = %s
    """, (user_id, course_id))
    progress = cur.fetchone()[0] if cur.rowcount > 0 else 0

    cur.close()
    conn.close()

    return render_template("course_page.html", 
                         course_name=course[0],
                         course_description=course[1],
                         course_image=course[2],
                         progress=progress)

@app.route("/get_groups/<int:course_id>")
def get_groups(course_id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            if session.get("role") == "teacher":
                cur.execute("""
                    SELECT DISTINCT g.group_name 
                    FROM groups g
                    WHERE g.course_id = %s AND g.teacher_id = %s
                    ORDER BY g.group_name
                """, (course_id, session["user_id"]))
            else:
                cur.execute("""
                    SELECT DISTINCT group_name 
                    FROM groups 
                    WHERE course_id = %s
                    ORDER BY group_name
                """, (course_id,))
                
            groups = [row[0] for row in cur.fetchall()]
            return jsonify({"success": True, "groups": groups})
    except Exception as e:
        app.logger.error(f"Error getting groups: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()

@app.route("/get_journal_data/<int:course_id>/<string:group_name>")
def get_journal_data(course_id, group_name):
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Get group info
            cur.execute("""
                SELECT g.id, g.teacher_id, u.name as teacher_name
                FROM groups g
                JOIN users u ON g.teacher_id = u.id
                WHERE g.course_id = %s AND g.group_name = %s
            """, (course_id, group_name))
            group = cur.fetchone()
            
            if not group:
                return jsonify({"success": False, "error": "Group not found"}), 404
                
            group_id, teacher_id, teacher_name = group

            # Get students in the group
            cur.execute("""
                SELECT u.id, u.name 
                FROM users u
                JOIN group_members gm ON u.id = gm.user_id
                WHERE gm.group_id = %s
                ORDER BY u.name
            """, (group_id,))
            students = [{"id": row[0], "name": row[1]} for row in cur.fetchall()]

            # Get attendance data
            cur.execute("""
                SELECT a.user_id, a.day, a.status, a.day_date
                FROM attendance a
                WHERE a.group_id = %s
                ORDER BY a.day
            """, (group_id,))
            
            attendance = {}
            for row in cur.fetchall():
                user_id, day, status, day_date = row
                if day not in attendance:
                    attendance[day] = []
                attendance[day].append({
                    "user_id": user_id,
                    "status": status,
                    "day_date": day_date.strftime("%Y-%m-%d") if day_date else None
                })

            # Get max day
            cur.execute("""
                SELECT MAX(day) FROM attendance
                WHERE group_id = %s
            """, (group_id,))
            max_day = cur.fetchone()[0] or 0

            return jsonify({
                "success": True,
                "group": {
                    "id": group_id,
                    "teacher_id": teacher_id,
                    "teacher_name": teacher_name
                },
                "students": students,
                "attendance": attendance,
                "max_day": max_day
            })
    except Exception as e:
        app.logger.error(f"Error getting journal data: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()


@app.route("/submit_attendance", methods=["POST"])
def submit_attendance():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        required_fields = ["course_id", "group_name", "day", "attendance"]
        if not all(field in data for field in required_fields):
            return jsonify({"success": False, "error": "Missing required fields"}), 400

        # Validate status values
        valid_statuses = {"i/e", "q/b", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"}
        for record in data["attendance"]:
            if record.get("status") and record["status"].lower() not in valid_statuses:
                return jsonify({
                    "success": False,
                    "error": f"Invalid status value: {record['status']}"
                }), 400

        conn = get_db_connection()
        with conn.cursor() as cur:
            # Get group ID
            cur.execute("""
                SELECT id FROM groups 
                WHERE course_id = %s AND group_name = %s
            """, (data["course_id"], data["group_name"]))
            group = cur.fetchone()
            if not group:
                return jsonify({"success": False, "error": "Group not found"}), 404
            group_id = group[0]

            # Update attendance records
            for record in data["attendance"]:
                if record.get("status"):  # Only update if status is provided
                    cur.execute("""
                        UPDATE attendance
                        SET status = %s
                        WHERE group_id = %s AND user_id = %s AND day = %s
                    """, (
                        record["status"].lower(),  # Store in lowercase
                        group_id,
                        record["user_id"],
                        data["day"]
                    ))

            conn.commit()
            return jsonify({"success": True, "message": "Attendance submitted successfully"})
    except Exception as e:
        conn.rollback()
        app.logger.error(f"Error submitting attendance: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()




@app.route("/delete_user_from_group/<int:group_id>/<int:user_id>", methods=["DELETE"])
def delete_user_from_group(group_id, user_id):
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Delete user's attendance records first
            cur.execute("""
                DELETE FROM attendance
                WHERE group_id = %s AND user_id = %s
            """, (group_id, user_id))

            # Then delete user from group
            cur.execute("""
                DELETE FROM group_members 
                WHERE group_id = %s AND user_id = %s
                RETURNING group_id
            """, (group_id, user_id))
            
            if not cur.fetchone():
                return jsonify({"error": "User not found in group"}), 404

            # Check if group is now empty
            cur.execute("""
                SELECT NOT EXISTS (
                    SELECT 1 FROM group_members WHERE group_id = %s
                )
            """, (group_id,))
            group_empty = cur.fetchone()[0]

            if group_empty:
                # Delete all attendance records for the group first
                cur.execute("""
                    DELETE FROM attendance
                    WHERE group_id = %s
                """, (group_id,))
                
                # Then delete the group
                cur.execute("""
                    DELETE FROM groups
                    WHERE id = %s
                """, (group_id,))

            conn.commit()
            return jsonify({
                "success": True,
                "group_deleted": group_empty,
                "message": "User deleted" + (" and group removed" if group_empty else "")
            })

    except Exception as e:
        conn.rollback()
        app.logger.error(f"Error deleting user from group: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route("/check_user_in_group/<int:group_id>/<int:user_id>")
def check_user_in_group(group_id, user_id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 1 FROM group_members 
                WHERE group_id = %s AND user_id = %s
            """, (group_id, user_id))
            exists = cur.fetchone() is not None
            return jsonify({"exists": exists})
    except Exception as e:
        app.logger.error(f"Error checking user in group: {e}")
        return jsonify({"exists": False, "error": str(e)}), 500
    finally:
        conn.close()







@app.route("/add_day", methods=["POST"])
def add_day():
    try:
        data = request.get_json()
        required_fields = ["course_id", "group_name", "day", "day_date", "teacher_id"]
        if not all(field in data for field in required_fields):
            return jsonify({"success": False, "error": "Missing required fields"}), 400

        conn = get_db_connection()
        with conn.cursor() as cur:
            # Get group info using course_id and group_name
            cur.execute("""
                SELECT g.id, gm.user_id
                FROM groups g
                JOIN group_members gm ON g.id = gm.group_id
                WHERE g.course_id = %s AND g.group_name = %s
            """, (data["course_id"], data["group_name"]))
            
            results = cur.fetchall()
            if not results:
                return jsonify({"success": False, "error": "Group not found or empty"}), 404
                
            group_id = results[0][0]
            user_ids = [row[1] for row in results]

            # First delete existing attendance for this day using group_id
            cur.execute("""
                DELETE FROM attendance
                WHERE group_id = %s AND day = %s
                RETURNING id
            """, (group_id, data["day"]))
            
            # Then insert new records
            for user_id in user_ids:
                try:
                    cur.execute("""
                        INSERT INTO attendance 
                        (user_id, group_id, course_id, teacher_id, day, day_date, status)
                        VALUES (%s, %s, %s, %s, %s, %s, NULL)
                        ON CONFLICT (user_id, group_id, day) DO NOTHING
                    """, (
                        user_id,
                        group_id,
                        data["course_id"],
                        data["teacher_id"],
                        data["day"],
                        data["day_date"]
                    ))
                except Exception as e:
                    conn.rollback()
                    app.logger.error(f"Error inserting attendance: {str(e)}")
                    return jsonify({"success": False, "error": str(e)}), 500

            conn.commit()
            return jsonify({
                "success": True, 
                "message": "Day activated successfully",
                "day": data["day"]
            })
    except Exception as e:
        conn.rollback()
        app.logger.error(f"Error adding day: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()
        
@app.route("/get_max_day/<int:course_id>/<string:group_name>")
def get_max_day_route(course_id, group_name):
    try:
        max_day = get_max_day(course_id, group_name)
        return jsonify({"success": True, "max_day": max_day})
    except Exception as e:
        print(f"Error fetching max day: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/create_group", methods=["POST"])
def create_group():
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        required_fields = ["course_id", "teacher_id", "group_name", "user_ids"]
        if not all(field in data for field in required_fields):
            return jsonify({"success": False, "error": "Missing required fields"}), 400

        conn = get_db_connection()
        with conn.cursor() as cur:
            # Check if group name exists globally
            cur.execute("""
                SELECT 1 FROM groups 
                WHERE LOWER(group_name) = LOWER(%s)
            """, (data["group_name"],))
            if cur.fetchone():
                return jsonify({
                    "success": False, 
                    "error": "Group name already exists in the system",
                    "existing": True
                }), 400

            # Validate teacher exists and is a teacher
            cur.execute("SELECT 1 FROM users WHERE id = %s AND role = 'teacher'", (data["teacher_id"],))
            if not cur.fetchone():
                return jsonify({"success": False, "error": "Invalid teacher ID"}), 400

            # Validate all user_ids are students
            cur.execute("""
                SELECT id FROM users 
                WHERE id = ANY(%s) AND role != 'student'
            """, (data["user_ids"],))
            non_students = cur.fetchall()
            if non_students:
                return jsonify({
                    "success": False,
                    "error": f"Cannot add non-students to group: {[ns[0] for ns in non_students]}"
                }), 400

            # Check if any students are already in a group for this course
            cur.execute("""
                SELECT u.id, u.name 
                FROM users u
                JOIN group_members gm ON u.id = gm.user_id
                JOIN groups g ON gm.group_id = g.id
                WHERE u.id = ANY(%s) AND g.course_id = %s
            """, (data["user_ids"], data["course_id"]))
            existing_members = cur.fetchall()
            
            if existing_members:
                return jsonify({
                    "success": False,
                    "error": "Some students are already in a group for this course",
                    "students": [{"id": row[0], "name": row[1]} for row in existing_members]
                }), 400

            # Reset sequence if needed
            cur.execute("""
                SELECT setval(pg_get_serial_sequence('groups', 'id'), 
                COALESCE((SELECT MAX(id) FROM groups), 0) + 1, false)
            """)

            # Assign teacher to course if not already
            cur.execute("""
                INSERT INTO teacher_courses (teacher_id, course_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """, (data["teacher_id"], data["course_id"]))

            # Create group
            cur.execute("""
                INSERT INTO groups (course_id, group_name, teacher_id)
                VALUES (%s, %s, %s)
                RETURNING id, group_name, course_id, teacher_id
            """, (data["course_id"], data["group_name"], data["teacher_id"]))
            group = cur.fetchone()

            # Add students to group
            for user_id in data["user_ids"]:
                try:
                    cur.execute("""
                        INSERT INTO group_members (group_id, user_id)
                        VALUES (%s, %s)
                    """, (group[0], user_id))
                except psycopg2.IntegrityError as e:
                    conn.rollback()
                    return jsonify({
                        "success": False,
                        "error": f"Student {user_id} is already in a group for this course"
                    }), 400

            conn.commit()
            return jsonify({
                "success": True,
                "group": {
                    "id": group[0],
                    "name": group[1],
                    "course_id": group[2],
                    "teacher_id": group[3]
                },
                "message": "Group created successfully"
            })

    except Exception as e:
        conn.rollback()
        app.logger.error(f"Error creating group: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()



        

@app.route("/teacher_dashboard")
def teacher_dashboard():
    if "user_id" not in session or session.get("role") != "teacher":
        return redirect(url_for("login"))

    teacher_id = session["user_id"]
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get teacher's courses
    cur.execute("""
        SELECT c.id, c.name 
        FROM courses c
        JOIN teacher_courses tc ON c.id = tc.course_id
        WHERE tc.teacher_id = %s
    """, (teacher_id,))
    courses = cur.fetchall()
    
    cur.close()
    conn.close()

    return render_template("teacher_dashboard.html", name=session["name"], courses=courses)

@app.route("/get_course_teachers/<int:course_id>")
def get_course_teachers(course_id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Use GROUP BY instead of DISTINCT for better performance
            cur.execute("""
                SELECT u.id, u.name 
                FROM users u
                JOIN teacher_courses tc ON u.id = tc.teacher_id
                WHERE tc.course_id = %s AND u.role = 'teacher'
                GROUP BY u.id, u.name
                ORDER BY u.name
            """, (course_id,))
            
            teachers = [{"id": row[0], "name": row[1]} for row in cur.fetchall()]
            return jsonify(teachers)
            
    except Exception as e:
        print(f"Error in get_course_teachers: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route("/get_teacher_groups/<int:course_id>/<int:teacher_id>")
def get_teacher_groups(course_id, teacher_id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT group_name 
                FROM groups 
                WHERE course_id = %s AND teacher_id = %s
                ORDER BY group_name
            """, (course_id, teacher_id))
            groups = [row[0] for row in cur.fetchall()]
            return jsonify({"success": True, "groups": groups})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()

@app.route("/get_all_teachers")
def get_all_teachers():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM users WHERE role = 'teacher' ORDER BY name")
            return jsonify([{"id": row[0], "name": row[1]} for row in cur.fetchall()])
    finally:
        conn.close()


@app.route("/check_teacher_groups/<int:course_id>/<int:teacher_id>")
def check_teacher_groups(course_id, teacher_id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM groups 
                    WHERE course_id = %s AND teacher_id = %s
                )
            """, (course_id, teacher_id))
            has_groups = cur.fetchone()[0]
            return jsonify({"has_groups": has_groups})
    except Exception as e:
        app.logger.error(f"Error checking teacher groups: {e}")
        return jsonify({"has_groups": False, "error": str(e)}), 500
    finally:
        conn.close()

@app.route("/get_course_teachers_with_groups/<int:course_id>")
def get_course_teachers_with_groups(course_id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT u.id, u.name 
                FROM users u
                JOIN groups g ON u.id = g.teacher_id
                WHERE g.course_id = %s
                ORDER BY u.name
            """, (course_id,))
            teachers = [{"id": row[0], "name": row[1]} for row in cur.fetchall()]
            return jsonify(teachers)
    except Exception as e:
        app.logger.error(f"Error getting teachers with groups: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


def cleanup_null_attendance():
    """Background task to clean up NULL attendance records"""
    while True:
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE attendance
                    SET status = 'n/s'
                    WHERE status IS NULL 
                    AND created_at < NOW() - INTERVAL '2 seconds'
                    RETURNING id, user_id, group_id, day
                """)
                updated = cur.rowcount
                if updated > 0:
                    print(f"{datetime.now()}: Cleaned {updated} NULL attendance records")
                conn.commit()
        except Exception as e:
            print(f"Error in cleanup job: {e}")
            if conn: conn.rollback()
        finally:
            if conn: conn.close()
        time.sleep(2)

@app.route("/register_teacher", methods=["POST"])
def register_teacher():
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = request.get_json()
        required_fields = ["name", "email", "phone", "birthday", "password"]
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        conn = get_db_connection()
        with conn.cursor() as cur:
            # Check if email already exists
            cur.execute("SELECT 1 FROM users WHERE email = %s", (data["email"],))
            if cur.fetchone():
                return jsonify({"error": "Email already registered"}), 400

            # Reset sequence to the next available ID
            cur.execute("SELECT setval(pg_get_serial_sequence('users', 'id'), COALESCE((SELECT MAX(id) FROM users), 0) + 1, false)")

            # Insert new teacher
            cur.execute(
                "INSERT INTO users (name, email, password, phone_number, birthday, role) "
                "VALUES (%s, %s, %s, %s, %s, 'teacher') RETURNING id",
                (data["name"], data["email"], data["password"], 
                 data["phone"], data["birthday"])
            )
            teacher_id = cur.fetchone()[0]
            conn.commit()
            
        return jsonify({"success": True, "teacher_id": teacher_id})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()



# Add to your imports
import uuid
from werkzeug.utils import secure_filename

# Add configuration
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB limit
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'txt', 'doc', 'docx', 'xls', 'xlsx', 'zip'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Add these routes
@app.route('/upload_file/<int:course_id>', methods=['POST'])
def upload_file(course_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Check file extension
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400
    
    # Check file size
    file.seek(0, os.SEEK_END)
    file_length = file.tell()
    if file_length > 5 * 1024 * 1024:  # 5MB limit
        return jsonify({'error': 'File size exceeds 5MB limit'}), 400
    file.seek(0)
    
    # Get additional parameters
    group_id = request.form.get('group_id')
    day = request.form.get('day')
    is_teacher = session.get('role') == 'teacher'

    # Validate teacher upload
    if is_teacher and (not group_id or not day):
        return jsonify({'error': 'Missing group/day for teacher upload'}), 400

    # For students, get current day
    if not is_teacher:
        cur.execute("""
            SELECT g.id FROM groups g
            JOIN group_members gm ON g.id = gm.group_id
            WHERE gm.user_id = %s AND g.course_id = %s
        """, (session['user_id'], course_id))
        group = cur.fetchone()
        if not group:
            return jsonify({'error': 'Not in a group'}), 400
        group_id = group[0]
        
        cur.execute("SELECT MAX(day) FROM attendance WHERE group_id = %s", (group_id,))
        day = cur.fetchone()[0] or 1

    # Insert with group/day info
    cur.execute("""
        INSERT INTO course_files 
        (course_id, group_id, user_id, file_name, file_path, 
         file_size, file_type, day, is_teacher_upload)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (course_id, group_id, session['user_id'], filename, unique_filename,
          file_size, file_type, day, is_teacher))



    try:
        # Ensure filename is safe
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Ensure upload directory exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Save the file
        file.save(file_path)
        
        # Verify file was saved
        if not os.path.exists(file_path):
            return jsonify({'error': 'Failed to save file'}), 500
            
        file_size = os.path.getsize(file_path)
        file_type = filename.rsplit('.', 1)[1].lower()
        
        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO course_files 
                    (course_id, user_id, file_name, file_path, file_size, file_type)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    course_id, 
                    session['user_id'],
                    filename,
                    unique_filename,
                    file_size,
                    file_type
                ))
                file_id = cur.fetchone()[0]
                conn.commit()
            
            return jsonify({
                'success': True,
                'message': 'File uploaded successfully',
                'file': {
                    'id': file_id,
                    'name': filename,
                    'path': unique_filename,
                    'size': file_size,
                    'type': file_type
                }
            })
        except Exception as e:
            if conn: conn.rollback()
            # Clean up the file if DB operation failed
            if os.path.exists(file_path):
                os.remove(file_path)
            app.logger.error(f"Database error: {str(e)}")
            return jsonify({'error': 'Database operation failed'}), 500
        finally:
            if conn: conn.close()
            
    except Exception as e:
        app.logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': 'File upload failed'}), 500

@app.route('/get_files/<int:course_id>')
def get_files(course_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            if session['role'] == 'teacher':
                cur.execute("""
                    SELECT cf.id, cf.file_name, cf.file_path, cf.file_size, cf.file_type, 
                           cf.uploaded_at, u.name as user_name
                    FROM course_files cf
                    JOIN users u ON cf.user_id = u.id
                    WHERE cf.course_id = %s
                    ORDER BY cf.uploaded_at DESC
                """, (course_id,))
            else:
                cur.execute("""
                    SELECT id, file_name, file_path, file_size, file_type, uploaded_at
                    FROM course_files
                    WHERE course_id = %s AND user_id = %s
                    ORDER BY uploaded_at DESC
                """, (course_id, session['user_id']))
            
            files = []
            for row in cur.fetchall():
                files.append({
                    'id': row[0],
                    'name': row[1],
                    'path': row[2],
                    'size': row[3],
                    'type': row[4],
                    'uploaded_at': row[5].strftime('%Y-%m-%d %H:%M'),
                    'user_name': row[6] if session['role'] == 'teacher' else None
                })
            
            return jsonify({'success': True, 'files': files})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/delete_file/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Check if user owns the file or is teacher/admin
            cur.execute("""
                SELECT user_id, file_path FROM course_files 
                WHERE id = %s
            """, (file_id,))
            file_data = cur.fetchone()
            
            if not file_data:
                return jsonify({'error': 'File not found'}), 404
                
            user_id, file_path = file_data
            
            if session['role'] not in ['admin', 'teacher'] and user_id != session['user_id']:
                return jsonify({'error': 'Unauthorized'}), 403
            
            # Delete file from filesystem
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], file_path))
            except OSError:
                pass  # File might already be deleted
                
            # Delete from database
            cur.execute("DELETE FROM course_files WHERE id = %s", (file_id,))
            conn.commit()
            
            return jsonify({'success': True, 'message': 'File deleted'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/get_group_files/<int:course_id>/<string:group_name>/<int:day>')
def get_group_files(course_id, group_name, day):
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT cf.id, cf.file_name, cf.file_path, cf.file_size, cf.file_type,
                       cf.day, u.name as user_name, cf.user_id
                FROM course_files cf
                JOIN users u ON cf.user_id = u.id
                JOIN groups g ON cf.group_id = g.id
                WHERE g.course_id = %s AND g.group_name = %s AND cf.day = %s
                ORDER BY cf.day DESC, u.name
            """, (course_id, group_name, day))
            files = [dict((cur.description[i][0], value) for i, value in enumerate(row)) 
                    for row in cur.fetchall()]
            return jsonify({"success": True, "files": files})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()



@app.route("/get_course_files/<int:course_id>")
def get_course_files(course_id):
    """Get all files available for a student in a course"""
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Get both teacher and student files for the course
            cur.execute("""
                (SELECT cf.id, cf.file_name, cf.file_path, cf.file_size, cf.file_type, 
                        cf.uploaded_at, cf.day, u.name as uploader, TRUE as is_teacher
                 FROM course_files cf
                 JOIN users u ON cf.user_id = u.id
                 JOIN groups g ON cf.group_id = g.id
                 JOIN group_members gm ON g.id = gm.group_id
                 WHERE gm.user_id = %s AND g.course_id = %s AND cf.is_teacher_upload = TRUE)
                
                UNION ALL
                
                (SELECT cf.id, cf.file_name, cf.file_path, cf.file_size, cf.file_type, 
                        cf.uploaded_at, cf.day, u.name as uploader, FALSE as is_teacher
                 FROM course_files cf
                 JOIN users u ON cf.user_id = u.id
                 WHERE cf.user_id = %s AND cf.course_id = %s AND cf.is_teacher_upload = FALSE)
                 
                ORDER BY day, uploaded_at DESC
            """, (session['user_id'], course_id, session['user_id'], course_id))
            
            files = []
            for row in cur:
                files.append({
                    "id": row[0],
                    "file_name": row[1],
                    "file_path": row[2],
                    "file_size": row[3],
                    "file_type": row[4],
                    "uploaded_at": row[5].strftime('%Y-%m-%d %H:%M'),
                    "day": row[6],
                    "uploader": row[7],
                    "is_teacher": row[8]
                })
            
            return jsonify({"success": True, "files": files})
    except Exception as e:
        app.logger.error(f"Error getting course files: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route('/upload_group_file', methods=['POST'])
def upload_group_file():
    if 'user_id' not in session or session.get("role") != "teacher":
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    try:
        course_id = request.form.get('course_id')
        group_name = request.form.get('group_name')
        day = request.form.get('day')
        
        # Get group ID
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id FROM groups 
                WHERE course_id = %s AND group_name = %s AND teacher_id = %s
            """, (course_id, group_name, session['user_id']))
            group = cur.fetchone()
            if not group:
                return jsonify({"success": False, "error": "Group not found"}), 404
            group_id = group[0]

            # File handling
            file = request.files['file']
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            
            # Insert into database
            cur.execute("""
                INSERT INTO course_files 
                (course_id, group_id, user_id, file_name, file_path, 
                 file_size, file_type, day, is_teacher_upload)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE)
                RETURNING id
            """, (
                course_id, group_id, session['user_id'], filename, unique_filename,
                os.path.getsize(file_path), filename.rsplit('.', 1)[1].lower(), day
            ))
            file_id = cur.fetchone()[0]
            conn.commit()
            
            return jsonify({
                "success": True,
                "message": "File uploaded successfully",
                "file_id": file_id
            })
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()

@app.route("/get_group_days_by_name/<string:group_name>")
def get_group_days_by_name(group_name):
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT a.day, MIN(a.day_date) as date
                FROM attendance a
                JOIN groups g ON a.group_id = g.id
                WHERE g.group_name = %s
                GROUP BY a.day
                ORDER BY a.day
            """, (group_name,))
            days = [{"day": row[0], "date": row[1].strftime('%Y-%m-%d')} for row in cur.fetchall()]
            return jsonify({"success": True, "days": days})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()



@app.route("/upload_student_file", methods=["POST"])
def upload_student_file():
    if 'user_id' not in session or session.get("role") != "student":
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file provided"}), 400
    
    file = request.files['file']
    course_id = request.form.get('course_id')
    
    if not course_id:
        return jsonify({"success": False, "error": "Missing course ID"}), 400

    try:
        course_id = int(course_id)
    except ValueError:
        return jsonify({"success": False, "error": "Invalid course ID"}), 400

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Get student's group in this course
            cur.execute("""
                SELECT g.id FROM groups g
                JOIN group_members gm ON g.id = gm.group_id
                WHERE gm.user_id = %s AND g.course_id = %s
            """, (session['user_id'], course_id))
            group = cur.fetchone()
            
            if not group:
                return jsonify({"success": False, "error": "Not in a group for this course"}), 400
            
            group_id = group[0]

            # File handling
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            upload_folder = app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)
            file_path = os.path.join(upload_folder, unique_filename)
            file.save(file_path)

            # Get current day from attendance
            cur.execute("""
                SELECT MAX(day) FROM attendance
                WHERE group_id = %s
            """, (group_id,))
            current_day = cur.fetchone()[0] or 1

            # Insert student file
            cur.execute("""
    INSERT INTO course_files 
    (course_id, group_id, user_id, file_name, file_path, file_size, file_type, day, is_teacher_upload)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, FALSE)
    RETURNING id
""", (
                course_id,
                group_id,
                session['user_id'],
                filename,
                unique_filename,
                os.path.getsize(file_path),
                filename.rsplit('.', 1)[1].lower(),
                current_day
            ))
            file_id = cur.fetchone()[0]
            conn.commit()

            return jsonify({
                "success": True,
                "message": "File uploaded successfully",
                "file_id": file_id
            })
    except Exception as e:
        if conn: conn.rollback()
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        app.logger.error(f"Student upload error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if conn: conn.close()






@app.route("/get_group_days/<int:group_id>")
def get_group_days(group_id):
    """Get all days with files for a group"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT day FROM course_files
                WHERE group_id = %s
                UNION
                SELECT DISTINCT day FROM attendance
                WHERE group_id = %s
                ORDER BY day
            """, (group_id, group_id))
            days = [row[0] for row in cur.fetchall()]
            return jsonify({"success": True, "days": days})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()


@app.route("/get_current_day/<int:group_id>")
def get_current_day(group_id):
    """Get current active day for student's group"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT MAX(day) FROM attendance
                WHERE group_id = %s
            """, (group_id,))
            current_day = cur.fetchone()[0] or 1
            return jsonify({"success": True, "day": current_day})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()




@app.route('/get_student_files/<int:course_id>')
def get_student_files(course_id):
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Get student's group
            cur.execute("""
                SELECT g.id FROM groups g
                JOIN group_members gm ON g.id = gm.group_id
                WHERE gm.user_id = %s AND g.course_id = %s
            """, (session['user_id'], course_id))
            group = cur.fetchone()
            if not group:
                return jsonify({"success": False, "error": "Not in a group"}), 400
            
            # Get all files for the group
            cur.execute("""
                SELECT cf.id, cf.file_name, cf.file_path, cf.file_size, cf.file_type,
                       cf.day, u.name as uploader, 
                       (cf.user_id = %s) as is_owner
                FROM course_files cf
                JOIN users u ON cf.user_id = u.id
                WHERE cf.group_id = %s
                ORDER BY cf.day DESC
            """, (session['user_id'], group[0]))
            files = [dict((cur.description[i][0], value) for i, value in enumerate(row)) 
                    for row in cur.fetchall()]
            return jsonify({"success": True, "files": files})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()




@app.route('/get_student_days/<int:course_id>')
def get_student_days(course_id):
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Get student's group
            cur.execute("""
                SELECT g.id FROM groups g
                JOIN group_members gm ON g.id = gm.group_id
                WHERE gm.user_id = %s AND g.course_id = %s
            """, (session['user_id'], course_id))
            group = cur.fetchone()
            if not group:
                return jsonify({"success": False, "error": "Not in a group"}), 400
            
            # Get available days
            cur.execute("""
                SELECT DISTINCT day FROM attendance
                WHERE group_id = %s
                UNION
                SELECT DISTINCT day FROM course_files
                WHERE group_id = %s
                ORDER BY day
            """, (group[0], group[0]))
            days = [row[0] for row in cur.fetchall()]
            return jsonify({"success": True, "days": days})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()


# Add these routes to app.py

@app.route("/get_group_days_for_files/<int:course_id>/<string:group_name>")
def get_group_days_for_files(course_id, group_name):
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT a.day, a.day_date 
                FROM attendance a
                JOIN groups g ON a.group_id = g.id
                WHERE g.course_id = %s AND g.group_name = %s
                ORDER BY a.day
            """, (course_id, group_name))
            days = [{"day": row[0], "date": row[1].strftime('%Y-%m-%d')} for row in cur.fetchall()]
            return jsonify({"success": True, "days": days})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()

@app.route("/upload_course_file", methods=["POST"])
def upload_course_file():
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    try:
        # Get form data
        course_id = request.form.get('course_id')
        group_name = request.form.get('group_name', None)
        day = request.form.get('day')
        is_teacher = session.get('role') == 'teacher'

        # Validate required fields
        if not course_id or not day:
            return jsonify({"success": False, "error": "Missing required fields"}), 400

        # Validate file presence
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "No file provided"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"success": False, "error": "No selected file"}), 400

        # File validation
        file.seek(0, os.SEEK_END)
        file_length = file.tell()
        file.seek(0)

        if file_length > 10 * 1024 * 1024:  # 10MB limit
            return jsonify({"success": False, "error": "File size exceeds 10MB limit"}), 400

        if not allowed_file(file.filename):
            return jsonify({"success": False, "error": "File type not allowed"}), 400

        conn = get_db_connection()
        with conn.cursor() as cur:
            group_id = None
            # Get group ID based on user type
            if is_teacher:
                # Teacher upload - validate group
                cur.execute("""
                    SELECT id FROM groups 
                    WHERE course_id = %s AND group_name = %s AND teacher_id = %s
                """, (course_id, group_name, session['user_id']))
                group = cur.fetchone()
                if not group:
                    return jsonify({"success": False, "error": "Group not found"}), 404
                group_id = group[0]
            else:
                # Student upload - get current group
                cur.execute("""
                    SELECT g.id FROM groups g
                    JOIN group_members gm ON g.id = gm.group_id
                    WHERE gm.user_id = %s AND g.course_id = %s
                """, (session['user_id'], course_id))
                group = cur.fetchone()
                if not group:
                    return jsonify({"success": False, "error": "Not in a group"}), 400
                group_id = group[0]

            # File handling
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            upload_folder = app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)
            file_path = os.path.join(upload_folder, unique_filename)
            
            # Save file to filesystem
            file.save(file_path)

            # Verify file was saved
            if not os.path.exists(file_path):
                return jsonify({"success": False, "error": "Failed to save file"}), 500

            # Insert into database
            cur.execute("""
                INSERT INTO course_files 
                (course_id, group_id, user_id, file_name, file_path, 
                 file_size, file_type, day, is_teacher_upload)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                course_id,
                group_id,
                session['user_id'],
                filename,
                unique_filename,
                os.path.getsize(file_path),
                filename.rsplit('.', 1)[1].lower(),
                day,
                is_teacher
            ))
            file_id = cur.fetchone()[0]
            conn.commit()

            return jsonify({
                "success": True,
                "file_id": file_id,
                "message": "File uploaded successfully"
            })

    except Exception as e:
        conn.rollback()
        app.logger.error(f"Upload error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route("/get_files_by_day/<int:course_id>/<int:day>")
def get_files_by_day(course_id, day):
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT cf.id, cf.file_name, cf.file_path, cf.file_size, 
                       cf.file_type, u.name as uploader, cf.is_teacher_upload
                FROM course_files cf
                JOIN users u ON cf.user_id = u.id
                WHERE cf.course_id = %s AND cf.day = %s
                ORDER BY cf.uploaded_at DESC
            """, (course_id, day))
            files = [dict((cur.description[i][0], value) for i, value in enumerate(row)) 
                    for row in cur.fetchall()]
            return jsonify({"success": True, "files": files})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()

@app.route("/delete_course_file/<int:file_id>", methods=["DELETE"])
def delete_course_file(file_id):
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Check permissions
            cur.execute("""
                SELECT user_id, file_path FROM course_files 
                WHERE id = %s
            """, (file_id,))
            file_data = cur.fetchone()
            if not file_data:
                return jsonify({"success": False, "error": "File not found"}), 404

            user_id, file_path = file_data
            if session['role'] != 'teacher' and user_id != session['user_id']:
                return jsonify({"success": False, "error": "Unauthorized"}), 403

            # Delete file from filesystem
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], file_path))
            except Exception as e:
                app.logger.error(f"Error deleting file: {str(e)}")

            # Delete from database
            cur.execute("DELETE FROM course_files WHERE id = %s", (file_id,))
            conn.commit()
            return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()


@app.route("/get_student_group/<int:course_id>/<int:user_id>")
def get_student_group(course_id, user_id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT g.group_name 
                FROM groups g
                JOIN group_members gm ON g.id = gm.group_id
                WHERE gm.user_id = %s AND g.course_id = %s
            """, (user_id, course_id))
            group = cur.fetchone()
            if not group:
                return jsonify({"success": False, "error": "Not in group"})
            return jsonify({"success": True, "group_name": group[0]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()


@app.route('/download_file/<path:filename>')
def download_file(filename):
    try:
        return send_from_directory(
            directory=app.config['UPLOAD_FOLDER'],
            path=filename,
            as_attachment=True,
            mimetype='application/octet-stream'  # Force binary download
        )
    except FileNotFoundError:
        app.logger.error(f"File not found: {filename}")
        return jsonify({"error": "File not found"}), 404


if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    cleanup_thread = threading.Thread(target=cleanup_null_attendance)
    cleanup_thread.daemon = True 
    cleanup_thread.start()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))  
