
from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash
)
from extensions import mysql

student_bp = Blueprint("students", __name__)


@student_bp.route("/")
def home():
    cur = mysql.connection.cursor()

    try:
        search = request.args.get("q", "").strip()

        query = """
            SELECT id, name, email, course, phone, age
            FROM students
        """
        params = ()

        if search:
            query += """
                WHERE name LIKE %s
                   OR email LIKE %s
                   OR course LIKE %s
                   OR phone LIKE %s
            """
            term = f"%{search}%"
            params = (term, term, term, term)

        query += " ORDER BY id"
        cur.execute(query, params)
        students = cur.fetchall()

        return render_template(
            "index.html",
            students=students,
            total_students=len(students),
            active_records=len(students),
            email_records=sum(1 for s in students if s[2]),
            search=search
        )
    finally:
        cur.close()


@student_bp.route("/add", methods=["GET", "POST"])
def add_student():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        course = request.form.get("course", "").strip()
        phone = request.form.get("phone", "").strip()
        age_text = request.form.get("age", "").strip()

        if not name:
            flash("Student name is required.", "danger")
            return render_template("add_student.html")

        age = None
        if age_text:
            try:
                age = int(age_text)
                if not 1 <= age <= 120:
                    raise ValueError
            except ValueError:
                flash("Enter a valid age between 1 and 120.", "danger")
                return render_template("add_student.html")

        cur = mysql.connection.cursor()
        try:
            cur.execute(
                """
                INSERT INTO students
                    (name, email, course, phone, age)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    name, email or None, course or None,
                    phone or None, age
                )
            )
            mysql.connection.commit()
            flash("Student added successfully.", "success")
            return redirect(url_for("students.home"))
        except Exception:
            mysql.connection.rollback()
            raise
        finally:
            cur.close()

    return render_template("add_student.html")


@student_bp.route("/edit/<int:student_id>", methods=["GET", "POST"])
def edit_student(student_id):
    cur = mysql.connection.cursor()

    try:
        cur.execute(
            """
            SELECT id, name, email, course, phone, age
            FROM students WHERE id = %s
            """,
            (student_id,)
        )
        student = cur.fetchone()

        if student is None:
            flash("Student not found.", "warning")
            return redirect(url_for("students.home"))

        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip()
            course = request.form.get("course", "").strip()
            phone = request.form.get("phone", "").strip()
            age_text = request.form.get("age", "").strip()

            if not name:
                flash("Student name is required.", "danger")
                return render_template(
                    "edit_student.html", student=student
                )

            age = None
            if age_text:
                try:
                    age = int(age_text)
                    if not 1 <= age <= 120:
                        raise ValueError
                except ValueError:
                    flash("Enter a valid age between 1 and 120.", "danger")
                    return render_template(
                        "edit_student.html", student=student
                    )

            cur.execute(
                """
                UPDATE students
                SET name=%s, email=%s, course=%s, phone=%s, age=%s
                WHERE id=%s
                """,
                (
                    name, email or None, course or None,
                    phone or None, age, student_id
                )
            )
            mysql.connection.commit()
            flash("Student updated successfully.", "success")
            return redirect(url_for("students.home"))

        return render_template("edit_student.html", student=student)

    except Exception:
        mysql.connection.rollback()
        raise
    finally:
        cur.close()


@student_bp.route("/delete/<int:student_id>", methods=["POST"])
def delete_student(student_id):
    cur = mysql.connection.cursor()
    try:
        cur.execute(
            "DELETE FROM students WHERE id = %s",
            (student_id,)
        )
        mysql.connection.commit()

        if cur.rowcount:
            flash("Student deleted successfully.", "success")
        else:
            flash("Student not found.", "warning")
    except Exception:
        mysql.connection.rollback()
        raise
    finally:
        cur.close()

    return redirect(url_for("students.home"))


@student_bp.route("/db-test")
def db_test():
    cur = mysql.connection.cursor()
    try:
        cur.execute("SELECT DATABASE()")
        return f"Connected successfully to: {cur.fetchone()[0]}"
    finally:
        cur.close()
