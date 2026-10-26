
from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import mysql

student_bp = Blueprint("students", __name__)


@student_bp.route("/")
def home():
    cur = mysql.connection.cursor()

    try:
        search = request.args.get("q", "").strip()

        query = """
            SELECT id, name, email
            FROM students
        """
        params = ()

        if search:
            query += """
                WHERE name LIKE %s OR email LIKE %s
            """
            term = f"%{search}%"
            params = (term, term)

        query += " ORDER BY id"
        cur.execute(query, params)
        students = cur.fetchall()

        total_students = len(students)
        email_records = sum(1 for student in students if student[2])

        return render_template(
            "index.html",
            students=students,
            total_students=total_students,
            active_records=total_students,
            email_records=email_records,
            search=search
        )
    finally:
        cur.close()


@student_bp.route("/add", methods=["GET", "POST"])
def add_student():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()

        if not name:
            flash("Student name is required.", "danger")
            return render_template("add_student.html")

        cur = mysql.connection.cursor()

        try:
            cur.execute(
                """
                INSERT INTO students (name, email)
                VALUES (%s, %s)
                """,
                (name, email or None)
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
        # Fetch the existing student
        cur.execute(
            """
            SELECT id, name, email
            FROM students
            WHERE id = %s
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

            if not name:
                flash("Student name is required.", "danger")
                return render_template(
                    "edit_student.html",
                    student=student
                )

            cur.execute(
                """
                UPDATE students
                SET name = %s, email = %s
                WHERE id = %s
                """,
                (name, email or None, student_id)
            )

            mysql.connection.commit()

            flash("Student updated successfully.", "success")
            return redirect(url_for("students.home"))

        return render_template(
            "edit_student.html",
            student=student
        )

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

        if cur.rowcount > 0:
            flash("Student deleted successfully.", "success")
        else:
            flash("Student not found.", "warning")

    except Exception:
        mysql.connection.rollback()
        raise

    finally:
        cur.close()

    return redirect(url_for("students.home"))
