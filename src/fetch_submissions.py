"""CLI: ดึงข้อมูลการส่งงาน (submissions) ไปบันทึกเป็น submissions.txt

Usage:
    python fetch_submissions.py                          # ใช้ค่า default ในโค้ด
    python fetch_submissions.py <course_id> <coursework_id>
"""

import os
import sys

from ta_auth import PROJECT_ROOT, get_classroom

COURSE_ID = "855107375121"
COURSEWORK_ID = "798287241596"


def main():
    course_id = sys.argv[1] if len(sys.argv) > 1 else COURSE_ID
    coursework_id = sys.argv[2] if len(sys.argv) > 2 else COURSEWORK_ID
    classroom = get_classroom()

    # ดึงรายชื่อนักศึกษาทั้งหมดในคอร์ส
    students_resp = classroom.courses().students().list(courseId=course_id).execute()
    students = {
        s["userId"]: s["profile"]["name"]["fullName"]
        for s in students_resp.get("students", [])
    }

    # ดึงข้อมูลการส่งงาน
    submissions_resp = (
        classroom.courses()
        .courseWork()
        .studentSubmissions()
        .list(courseId=course_id, courseWorkId=coursework_id)
        .execute()
    )

    submissions = submissions_resp.get("studentSubmissions", [])

    header = f"{'ชื่อนักศึกษา':<40} {'สถานะ':<20} {'ชื่อไฟล์'}"
    separator = "-" * 100
    lines = [header, separator]

    for sub in submissions:
        student_name = students.get(sub["userId"], sub["userId"])
        state = sub.get("state", "UNKNOWN")

        attachments = sub.get("assignmentSubmission", {}).get("attachments", [])
        filenames = [
            a["driveFile"]["title"] for a in attachments if "driveFile" in a
        ]

        if filenames:
            for filename in filenames:
                lines.append(f"{student_name:<40} {state:<20} {filename}")
        else:
            lines.append(f"{student_name:<40} {state:<20} (ไม่มีไฟล์)")

    output = "\n".join(lines)
    print(output)

    out_path = os.path.join(PROJECT_ROOT, "submissions.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(output)
    print(f"\nบันทึกไฟล์ {out_path} เรียบร้อยแล้ว")


if __name__ == "__main__":
    main()