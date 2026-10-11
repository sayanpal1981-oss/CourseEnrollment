import os
import re
import subprocess
from flask import Flask, render_template, request, jsonify

PROLOG_PATH = None

COMMON_WINDOWS_PATHS = [
    r"C:\Program Files\swipl\bin\swipl.exe",
    r"C:\Program Files (x86)\swipl\bin\swipl.exe",
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PL_FILE = os.path.join(BASE_DIR, "enrollment.pl")

app = Flask(__name__)

SAFE_ATOM = re.compile(r"^[a-zA-Z0-9_]+$")


class PrologError(Exception):
    pass


def find_prolog_executable():
    if PROLOG_PATH and os.path.isfile(PROLOG_PATH):
        return PROLOG_PATH

    for candidate in COMMON_WINDOWS_PATHS:
        if os.path.isfile(candidate):
            return candidate

    return "swipl"


def sanitize_atom(value):
    if value is None or not SAFE_ATOM.match(str(value)):
        raise ValueError(f"Invalid identifier: {value!r}")
    return str(value)


def run_prolog_goal(goal):
    exe = find_prolog_executable()

    command = [exe, "-q", "-f", PL_FILE, "-g", goal, "-t", "halt"]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError:
        raise PrologError(
            "SWI-Prolog was not found. Install it from "
            "https://www.swi-prolog.org/Download.html, or set "
            "PROLOG_PATH at the top of app.py to the full path of "
            "swipl.exe."
        )
    except subprocess.TimeoutExpired:
        raise PrologError("The Prolog query took too long to run.")

    if result.returncode != 0:
        raise PrologError(
            f"Prolog reported an error: {result.stderr.strip() or 'unknown error'}"
        )

    return result.stdout.strip()


def run_and_get_lines(goal):
    output = run_prolog_goal(goal)
    lines = [line for line in output.splitlines() if line.strip()]

    if lines and lines[0].startswith("ERROR:"):
        code = lines[0].split(":", 1)[1]
        messages = {
            "no_such_student": "That student does not exist.",
            "no_such_course": "That course does not exist.",
        }
        raise PrologError(messages.get(code, "Invalid request."))

    return lines


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/stats")
def api_stats():
    try:
        lines = run_and_get_lines("print_stats")
        students, courses, enrollments = lines[0].split("|")
        return jsonify({
            "students": int(students),
            "courses": int(courses),
            "enrollments": int(enrollments),
        })
    except PrologError as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/students")
def api_students():
    try:
        lines = run_and_get_lines("print_students")
        students = []
        for line in lines:
            sid, name, dept = line.split("|")
            students.append({"id": sid, "name": name, "department": dept})
        return jsonify(students)
    except PrologError as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/courses")
def api_courses():
    try:
        lines = run_and_get_lines("print_courses")
        courses = []
        for line in lines:
            cid, name, dept, credits = line.split("|")
            courses.append({
                "id": cid, "name": name, "department": dept,
                "credits": int(credits),
            })
        return jsonify(courses)
    except PrologError as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/departments")
def api_departments():
    try:
        lines = run_and_get_lines("print_departments")
        return jsonify(lines)
    except PrologError as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/department/<dept>/students")
def api_department_students(dept):
    try:
        dept = sanitize_atom(dept)
        lines = run_and_get_lines(f"print_department_students({dept})")
        students = []
        for line in lines:
            sid, name, d = line.split("|")
            students.append({"id": sid, "name": name, "department": d})
        return jsonify(students)
    except ValueError:
        return jsonify({"error": "Invalid department."}), 400
    except PrologError as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/department/<dept>/courses")
def api_department_courses(dept):
    try:
        dept = sanitize_atom(dept)
        lines = run_and_get_lines(f"print_department_courses({dept})")
        courses = []
        for line in lines:
            cid, name, credits = line.split("|")
            courses.append({"id": cid, "name": name, "credits": int(credits)})
        return jsonify(courses)
    except ValueError:
        return jsonify({"error": "Invalid department."}), 400
    except PrologError as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/student/<student_id>/courses")
def api_student_courses(student_id):
    try:
        student_id = sanitize_atom(student_id)
        lines = run_and_get_lines(f"print_student_courses({student_id})")
        courses = []
        for line in lines:
            cid, name, credits = line.split("|")
            courses.append({"id": cid, "name": name, "credits": int(credits)})
        return jsonify(courses)
    except ValueError:
        return jsonify({"error": "Invalid student id."}), 400
    except PrologError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/course/<course_id>/students")
def api_course_students(course_id):
    try:
        course_id = sanitize_atom(course_id)
        lines = run_and_get_lines(f"print_course_students({course_id})")
        students = []
        for line in lines:
            sid, name, dept = line.split("|")
            students.append({"id": sid, "name": name, "department": dept})
        return jsonify(students)
    except ValueError:
        return jsonify({"error": "Invalid course id."}), 400
    except PrologError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/course/<course_id>/credits")
def api_course_credits(course_id):
    try:
        course_id = sanitize_atom(course_id)
        lines = run_and_get_lines(f"print_course_credits({course_id})")
        return jsonify({"course_id": course_id, "credits": int(lines[0])})
    except ValueError:
        return jsonify({"error": "Invalid course id."}), 400
    except PrologError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/check-enrollment")
def api_check_enrollment():
    student_id = request.args.get("student", "")
    course_id = request.args.get("course", "")
    try:
        student_id = sanitize_atom(student_id)
        course_id = sanitize_atom(course_id)
        lines = run_and_get_lines(
            f"print_check_enrollment({student_id}, {course_id})"
        )
        enrolled = lines[0] == "true"
        return jsonify({
            "student_id": student_id,
            "course_id": course_id,
            "enrolled": enrolled,
        })
    except ValueError:
        return jsonify({"error": "Please choose both a student and a course."}), 400
    except PrologError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/common-courses")
def api_common_courses():
    s1 = request.args.get("student1", "")
    s2 = request.args.get("student2", "")
    try:
        s1 = sanitize_atom(s1)
        s2 = sanitize_atom(s2)
        if s1 == s2:
            return jsonify({"error": "Please choose two different students."}), 400
        lines = run_and_get_lines(f"print_common_courses({s1}, {s2})")
        courses = []
        for line in lines:
            cid, name, credits = line.split("|")
            courses.append({"id": cid, "name": name, "credits": int(credits)})
        return jsonify(courses)
    except ValueError:
        return jsonify({"error": "Please choose two students."}), 400
    except PrologError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/enroll", methods=["POST"])
def api_enroll():
    data = request.get_json(silent=True) or {}
    student_id = data.get("student_id", "")
    course_id = data.get("course_id", "")

    try:
        student_id = sanitize_atom(student_id)
        course_id = sanitize_atom(course_id)
    except ValueError:
        return jsonify({"success": False,
                         "message": "Please choose both a student and a course."}), 400

    try:
        lines = run_and_get_lines(f"print_can_enroll({student_id}, {course_id})")
        verdict = lines[0]
    except PrologError as e:
        return jsonify({"success": False, "message": str(e)}), 500

    if verdict == "invalid_student":
        return jsonify({"success": False, "message": "That student does not exist."}), 400
    if verdict == "invalid_course":
        return jsonify({"success": False, "message": "That course does not exist."}), 400
    if verdict == "already_enrolled":
        return jsonify({"success": False,
                         "message": "This student is already enrolled in that course."}), 409

    try:
        with open(PL_FILE, "a", encoding="utf-8") as f:
            f.write(f"enrolled({student_id}, {course_id}).\n")
    except OSError as e:
        return jsonify({"success": False,
                         "message": f"Could not save enrollment: {e}"}), 500

    return jsonify({
        "success": True,
        "message": "Student enrolled successfully.",
        "student_id": student_id,
        "course_id": course_id,
    })


if __name__ == "__main__":
    app.run(debug=True)
