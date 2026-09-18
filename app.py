import os
import re
import requests as http_requests
from flask import Flask, render_template, request, jsonify
from googleapiclient.errors import HttpError

from src.ta_auth import get_classroom, get_id_token

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ta-classroom-secret")

CLASS_ID = os.environ.get("CLASS_ID", "2569CP412703")

EXERCISE_MAP = {
    "lab02": {"id": "12", "max": 1},
    "lab03": {"id": "15", "max": 1},
    "lab04": {"id": "19", "max": 4},
    "lab05": {"id": "21", "max": 1},
    "lab06": {"id": "22", "max": 1},
    "lab07": {"id": "30", "max": 1},
    "lab08": {"id": "42", "max": 1},
    "lab09": {"id": "47", "max": 1},
}

STATE_LABEL = {
    "TURNED_IN": ("ส่งแล้ว", "success"),
    "CREATED": ("ยังไม่ส่ง", "danger"),
    "RETURNED": ("ส่งคืนแล้ว", "warning"),
    "RECLAIMED_BY_STUDENT": ("ดึงกลับ", "secondary"),
}


def extract_last4(filename):
    name = re.sub(r'\.[^.]+$', '', filename)
    digits = re.sub(r'[^0-9]', '', name)
    match = re.search(r'(6[5-8]\d{8})', digits)
    if match:
        return match.group(1)[-4:]
    return None


def guess_exercise_id(coursework_title):
    match = re.search(r'lab\s*0?(\d+)', coursework_title.lower())
    if match:
        key = f"lab{int(match.group(1)):02d}"
        info = EXERCISE_MAP.get(key)
        if info:
            return info["id"], info["max"]
    return None, 1


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/courses")
def courses():
    classroom = get_classroom()
    resp = classroom.courses().list().execute()
    courses = resp.get("courses", [])
    return render_template("courses.html", courses=courses)


@app.route("/coursework")
def coursework():
    course_id = request.args.get("course_id", "855107375121")
    classroom = get_classroom()
    resp = classroom.courses().courseWork().list(courseId=course_id).execute()
    works = resp.get("courseWork", [])
    return render_template("coursework.html", works=works, course_id=course_id)


@app.route("/submissions")
def submissions():
    course_id = request.args.get("course_id", "")
    coursework_id = request.args.get("coursework_id", "")
    classroom = get_classroom()

    courses_resp = classroom.courses().list().execute()
    all_courses = courses_resp.get("courses", [])

    all_works = []
    grouped = {}
    max_points = None

    if course_id:
        works_resp = classroom.courses().courseWork().list(courseId=course_id).execute()
        all_works = works_resp.get("courseWork", [])

    if course_id and coursework_id:
        try:
            work = classroom.courses().courseWork().get(
                courseId=course_id, id=coursework_id
            ).execute()
        except HttpError:
            work = None
            coursework_id = ""
        if work:
            max_points = work.get("maxPoints")
            exercise_id, score_max = guess_exercise_id(work.get("title", ""))

            students_resp = classroom.courses().students().list(courseId=course_id).execute()
            students = {
                s["userId"]: s["profile"]["name"]["fullName"]
                for s in students_resp.get("students", [])
            }
            subs_resp = (
                classroom.courses()
                .courseWork()
                .studentSubmissions()
                .list(courseId=course_id, courseWorkId=coursework_id)
                .execute()
            )
            for sub in subs_resp.get("studentSubmissions", []):
                state = sub.get("state", "UNKNOWN")
                label, badge = STATE_LABEL.get(state, (state, "secondary"))
                attachments = sub.get("assignmentSubmission", {}).get("attachments", [])
                filenames = [
                    {"title": a["driveFile"].get("title", ""), "link": a["driveFile"].get("alternateLink", "")}
                    for a in attachments if "driveFile" in a
                ]
                entry = {
                    "submission_id": sub["id"],
                    "state": state,
                    "name": students.get(sub["userId"], sub["userId"]),
                    "filenames": filenames if filenames else [{"title": "(ไม่มีไฟล์)", "link": ""}],
                    "badge": badge,
                    "assigned_grade": sub.get("assignedGrade"),
                    "draft_grade": sub.get("draftGrade"),
                    "last4": extract_last4(filenames[0]["title"]) if filenames else None,
                    "exercise_id": exercise_id,
                    "max_points": score_max,
                }
                grouped.setdefault((state, label, badge), []).append(entry)

    active_state = request.args.get("state", "")
    all_entries = [e for entries in grouped.values() for e in entries]
    filtered_entries = (
        [e for e in all_entries if e["state"] == active_state]
        if active_state else all_entries
    ) if grouped else None

    return render_template(
        "submissions.html",
        grouped=grouped,
        all_courses=all_courses,
        all_works=all_works,
        course_id=course_id,
        coursework_id=coursework_id,
        max_points=max_points,
        active_state=active_state,
        filtered_entries=filtered_entries,
    )


@app.route("/submit_score", methods=["POST"])
def submit_score():
    last4 = request.form.get("last4", "").strip()
    score = request.form.get("score", "").strip()
    exercise_id = request.form.get("exercise_id", "").strip()

    try:
        id_token = get_id_token()
        resp = http_requests.post(
            "https://getscore1.com/ta_score.php",
            json={
                "action": "submit",
                "classid": CLASS_ID,
                "exercise_id": exercise_id,
                "id_token": id_token,
                "last4": last4,
                "score": score,
            },
            timeout=10,
        )
        data = resp.json()
        return jsonify({"ok": True, "data": data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


if __name__ == "__main__":
    app.run(debug=True)
