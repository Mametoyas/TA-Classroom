"""CLI: แสดงรายการคอร์สทั้งหมดใน Google Classroom account นี้
Usage:
    python check_courses.py
"""

from ta_auth import get_classroom


def main():
    classroom = get_classroom()
    resp = classroom.courses().list().execute()
    courses = resp.get("courses", [])

    if not courses:
        print("ไม่พบคอร์สใดๆ ใน account นี้")
        return

    print(f"{'courseId':<30} {'ชื่อคอร์ส'}")
    print("-" * 80)
    for c in courses:
        print(f"{c['id']:<30} {c['name']}")


if __name__ == "__main__":
    main()