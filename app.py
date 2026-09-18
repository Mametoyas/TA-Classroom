import os
import re
import time

from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, send_from_directory
from googleapiclient.errors import HttpError

from src.ta_auth import get_classroom

# โหลด .env (root) ก่อนอ่าน env var — sensitive data (SECRET_KEY, CLASS_ID, ...)
# อยู่ใน .env ซึ่งถูก gitignore แล้ว (ดู .env.example เป็นตัวอย่าง)
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ta-classroom-secret")

CLASS_ID = os.environ.get("CLASS_ID", "2569CP412703")

# รายวิชาที่ "ให้คะแนนเว็บ (getscore1)" ใช้ได้ — วิชาอื่นดูได้แค่งาน (ยังเปิดคลาสรูมได้)
WEB_GRADE_COURSES = {
    c.strip()
    for c in os.environ.get(
        "WEB_GRADE_COURSES", "855107375121,855274641019,855273686370"
    ).split(",")
    if c.strip()
}

EXTENSION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "extension")


def _api_call(fn, retries=3):
    """เรียก Google Classroom API พร้อม retry อัตโนมัติเมื่อเจอ error ชั่วคราว (5xx/429)"""
    for attempt in range(retries):
        try:
            return fn()
        except HttpError as e:
            status = getattr(e.resp, "status", None)
            if status in (429, 500, 502, 503, 504) and attempt < retries - 1:
                time.sleep(1.0 * (2 ** attempt))
                continue
            raise


@app.errorhandler(HttpError)
def handle_classroom_error(e):
    status = getattr(getattr(e, "resp", None), "status", None)
    if status == 403:
        message = (
            "สิทธิ์ไม่เพียงพอที่จะเข้าถึง Google Classroom (HTTP 403)<br>"
            "ตรวจว่าใช้บัญชี TA ที่ถูกต้อง และลบ token.json เพื่อ authorize ใหม่"
        )
    elif status in (429, 500, 502, 503, 504):
        message = (
            f"Google Classroom API ติดขัดชั่วคราว (HTTP {status})<br>"
            "นี่เป็น error ฝั่ง Google เอง — รอสักครู่แล้วกดปุ่มรีเฟรช"
        )
    else:
        message = f"Google Classroom API error (HTTP {status}): {e}"
    return render_template("error.html", message=message), status or 500

EXERCISE_MAP = {
    "lab01": {"id": "8", "max": 1},
    "lab02": {"id": "12", "max": 1},
    "lab03": {"id": "15", "max": 1},
    "lab04": {"id": "19", "max": 4},
    "lab05": {"id": "21", "max": 1},
    "lab06": {"id": "22", "max": 1},
    "lab07": {"id": "30", "max": 1},
    "lab08": {"id": "42", "max": 1},
    "lab09": {"id": "47", "max": 1},
    "lab10": {"id": "48", "max": 1},
}

# Reverse map: exercise_id -> คะแนนสูงสุด (ใช้ตรวจสอบขอบเขตคะแนน)
EXERCISE_ID_TO_MAX = {info["id"]: info["max"] for info in EXERCISE_MAP.values()}

# Bookmarklet "TA Autofill" — รันบนหน้า getscore1.com เท่านั้น
# อ่าน hash (#classid=..&exercise_id=..&last4=..&score=..) แล้วกรอกฟอร์ม + ส่งอัตโนมัติ
# ต้องล็อกอิน Google บนเว็บก่อน (เว็บใช้ session ตัวเอง ยอมรับแค่ credential ของเว็บเท่านั้น)
BOOKMARKLET_SCRIPT = """javascript:(function(){
  var p={};
  (location.hash||'').replace(/^#/,'').split('&').forEach(function(kv){var i=kv.indexOf('=');if(i>-1)p[kv.slice(0,i)]=decodeURIComponent(kv.slice(i+1));});
  function $(id){return document.getElementById(id);}
  function pick(sel,val,ev){for(var i=0;i<sel.options.length;i++){if(sel.options[i].value===val){sel.selectedIndex=i;break;}}if(ev)sel.dispatchEvent(new Event('change'));}
  function waitFor(cond,cb,tryN){if(cond()){cb();}else if(tryN){setTimeout(function(){waitFor(cond,cb,tryN-1);},200);}else{alert('โหลดข้อมูลไม่สำเร็จ — ลองใหม่อีกครั้ง');}}
  var app=$('appCard');
  if(!app){alert('หน้านี้ไม่ใช่ ta_score.php');return;}
  if(app.classList.contains('hidden')){alert('กรุณาเข้าสู่ระบบ getscore1 ก่อน (ปุ่มล็อกอิน Google)');return;}
  if(!p.classid||!p.exercise_id){
    alert('หน้านี้ยังไม่มีข้อมูลนักศึกษา (ลิงก์ไม่ครบ)\n\nวิธีใช้ที่ถูกต้อง:\n1) ไปหน้า Submissions ในโปรเจกต์\n2) กดปุ่ม ให้คะแนนเว็บ\n4) ถ้าแค่เปิดเว็บเองเฉยๆ (เช่น กดล็อกอินก่อน) จะกดไม่ได้ผล - ต้องเปิดผ่านปุ่ม ให้คะแนนเว็บ ก่อน');
    return;
  }
  pick($('courseSel'),p.classid,true);
  waitFor(function(){return $('exSel').options.length>1;},function(){
    pick($('exSel'),p.exercise_id,true);
    waitFor(function(){return $('score').value!=='';},function(){
      if(p.score)$('score').value=p.score;
      if(p.last4)$('last4').value=p.last4;
      var f=$('scoreForm');
      if(f.requestSubmit)f.requestSubmit();else if(f.submit)f.submit();
    },20);
  },40);
})();"""

STATE_LABEL = {
    "TURNED_IN": ("ส่งแล้ว", "success"),
    "CREATED": ("ยังไม่ส่ง", "danger"),
    "RETURNED": ("ส่งคืนแล้ว", "warning"),
    "RECLAIMED_BY_STUDENT": ("ดึงกลับ", "secondary"),
}


def extract_last4(filename):
    """ดึง last4 จากชื่อไฟล์ที่ต้องมีรหัสนักศึกษา (6[5-8]... ความยาว 9-10 หลัก)

    เช่น Lab01_663380518-4_ชื่อ นามสกุล.ipynb -> "5184"
        Lab01_663380518_ชื่อ นามสกุล.ipynb   -> "0518"
        ชื่อไฟล์ที่ไม่มีรหัสนักศึกษา           -> None
    """
    name = re.sub(r'\.[^.]+$', '', filename)
    # match เฉพาะล็อกที่ขึ้นต้นด้วย 6[5-8] และอยู่หลังอักษร/ขีด (กันเลข "Lab" หลอก)
    match = re.search(r'(?<!\d)(?:6[5-8]\d{8}|6[5-8]\d{7}(?:[-_]\d)?)(?!\d)', name)
    if match:
        return re.sub(r'\D', '', match.group(0))[-4:]
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
    resp = _api_call(lambda: classroom.courses().list().execute())
    courses = resp.get("courses", [])
    return render_template("courses.html", courses=courses)


@app.route("/coursework")
def coursework():
    course_id = request.args.get("course_id", "855107375121")
    classroom = get_classroom()
    resp = _api_call(
        lambda: classroom.courses().courseWork().list(courseId=course_id).execute()
    )
    works = resp.get("courseWork", [])
    return render_template("coursework.html", works=works, course_id=course_id)


@app.route("/bookmarklet")
def bookmarklet():
    return render_template(
        "bookmarklet.html",
        bookmarklet=" ".join(BOOKMARKLET_SCRIPT.strip().split()),
    )


@app.route("/extension/<path:filename>")
def extension_file(filename):
    """แจกไฟล์ extension (manifest.json, content.js) ให้โหลดไปติดตั้งแบบ Load unpacked"""
    return send_from_directory(EXTENSION_DIR, filename, as_attachment=True)


@app.route("/submissions")
def submissions():
    course_id = request.args.get("course_id", "")
    coursework_id = request.args.get("coursework_id", "")
    classroom = get_classroom()

    courses_resp = _api_call(lambda: classroom.courses().list().execute())
    all_courses = courses_resp.get("courses", [])

    all_works = []
    grouped = {}
    max_points = None

    if course_id:
        works_resp = _api_call(
            lambda: classroom.courses().courseWork().list(courseId=course_id).execute()
        )
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

            students_resp = _api_call(
                lambda: classroom.courses().students().list(courseId=course_id).execute()
            )
            students = {
                s["userId"]: s["profile"]["name"]["fullName"]
                for s in students_resp.get("students", [])
            }
            subs_resp = _api_call(
                lambda: classroom.courses()
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
                    "classroom_link": work.get("alternateLink"),
                }
                grouped.setdefault((state, label, badge), []).append(entry)

    active_state = request.args.get("state", "")
    all_entries = [e for entries in grouped.values() for e in entries]
    filtered_entries = (
        [e for e in all_entries if e["state"] == active_state]
        if active_state else all_entries
    ) if grouped else None

    # ให้คะแนนเว็บได้เฉพาะวิชาใน WEB_GRADE_COURSES เท่านั้น (วิชาอื่นดูได้แค่งาน)
    can_web_grade = course_id in WEB_GRADE_COURSES

    # สำหรับปุ่ม "ให้คะแนนทุกคน": เฉพาะคนที่ส่งแล้ว + มี exercise_id
    # มี last4 -> ให้คะแนนได้ / ไม่มี last4 (ชื่อไฟล์ผิดรูปแบบ) -> ข้าม + แจ้งใน noti
    grade_entries = filtered_entries if can_web_grade else []
    grade_items = [
        {
            "name": e["name"],
            "last4": e["last4"],
            "exercise_id": e["exercise_id"],
            "score": e["max_points"],
            "key": f"{coursework_id}_{e['submission_id']}",
        }
        for e in grade_entries
        if e["state"] == "TURNED_IN" and e["exercise_id"] and e["last4"]
    ]
    grade_skipped = [
        e["name"]
        for e in grade_entries
        if e["state"] == "TURNED_IN" and e["exercise_id"] and not e["last4"]
    ]

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
        grade_items=grade_items,
        grade_skipped=grade_skipped,
        can_web_grade=can_web_grade,
        class_id=CLASS_ID,
    )


@app.route("/grade_classroom", methods=["POST"])
def grade_classroom():
    """ให้คะแนนนักศึกษาใน Google Classroom โดยตรง (patch assignedGrade + return)"""
    course_id = request.form.get("course_id", "").strip()
    coursework_id = request.form.get("coursework_id", "").strip()
    submission_id = request.form.get("submission_id", "").strip()
    score = request.form.get("score", "").strip()

    try:
        score_val = float(score)
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "คะแนนไม่ถูกต้อง"}), 400

    try:
        classroom = get_classroom()
        # ตรวจสอบคะแนนเทียบกับคะแนนเต็มของแลปนี้ (EXERCISE_MAP)
        work = classroom.courses().courseWork().get(
            courseId=course_id, id=coursework_id
        ).execute()
        _, max_allowed = guess_exercise_id(work.get("title", ""))
        if max_allowed is not None and not (0 <= score_val <= max_allowed):
            return jsonify({
                "ok": False,
                "error": f"คะแนนต้องอยู่ระหว่าง 0-{max_allowed} (เต็มของแลปนี้)",
            }), 400
        # 1) ตั้งคะแนน (grade)
        classroom.courses().courseWork().studentSubmissions().patch(
            courseId=course_id,
            courseWorkId=coursework_id,
            id=submission_id,
            body={"assignedGrade": score_val, "draftGrade": score_val},
            updateMask="assignedGrade,draftGrade",
        ).execute()
        # 2) ส่งคืนให้นักศึกษา (state -> RETURNED) เพื่อแสดงคะแนน
        classroom.courses().courseWork().studentSubmissions().return_(
            courseId=course_id,
            courseWorkId=coursework_id,
            id=submission_id,
        ).execute()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/submit_score", methods=["POST"])
def submit_score():
    """**Deprecated** — getscore1.com ยอมรับเฉพาะ session/link id จากปุ่ม Google Sign-In ของเว็บเอง
    backend ไม่สามารถส่งคะแนนแทนได้ (auth:false เสมอ) ให้ใช้ปุ่ม 'ให้คะแนนเว็บ' + bookmarklet TA Autofill แทน"""
    last4 = request.form.get("last4", "").strip()
    score = request.form.get("score", "").strip()
    exercise_id = request.form.get("exercise_id", "").strip()

    if not last4:
        return jsonify({"ok": False, "error": "ไม่พบรหัสนักศึกษา (ขึ้นต้น 65-68) ในชื่อไฟล์"}), 400

    try:
        score_val = float(score)
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "คะแนนไม่ถูกต้อง"}), 400

    max_allowed = EXERCISE_ID_TO_MAX.get(exercise_id)
    if max_allowed is not None and not (0 <= score_val <= max_allowed):
        return jsonify({
            "ok": False,
            "error": f"คะแนนต้องอยู่ระหว่าง 0-{max_allowed} (เต็มของแลปนี้)",
        }), 400

    return jsonify({
        "ok": False,
        "error": "ไม่สามารถส่งคะแนนผ่าน backend ได้ — getscore1.com ต้องใช้ session ในเบราว์เซอร์ของตัวเอง "
                 "(ล็อกอิน Google บนเว็บ แล้วกด bookmarklet TA Autofill)",
    }), 501


if __name__ == "__main__":
    app.run(debug=True)
