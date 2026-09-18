"""CLI: แสดงรายการงาน (course work) ของคอร์สหนึ่ง

Usage:
    python check_coursework.py                 # ใช้ COURSE_ID default ในโค้ด
    python check_coursework.py <course_id>     # ระบุ course_id เอง
"""

import sys

from ta_auth import get_classroom

COURSE_ID = "855107375121"


def main():
    course_id = sys.argv[1] if len(sys.argv) > 1 else COURSE_ID
    classroom = get_classroom()

    resp = classroom.courses().courseWork().list(courseId=course_id).execute()
    works = resp.get("courseWork", [])

    if not works:
        print("ไม่พบงานใดๆ ในคอร์สนี้")
        return

    print(f"{'courseWorkId':<25} {'ชื่องาน'}")
    print("-" * 80)
    for w in works:
        print(f"{w['id']:<25} {w['title']}")


if __name__ == "__main__":
    main()