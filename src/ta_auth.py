"""
Shared Google OAuth helper — ใช้ร่วมกันระหว่าง web app และ CLI scripts

- รวม SCOPES ทั้งหมดไว้จุดเดียว
- get_credentials(): โหลด/สร้าง token.json อัตโนมัติ (เปิดเบราว์เซอร์ครั้งแรก)
- get_classroom(): สร้าง Classroom API client
- get_id_token(): ดึง id_token (ใช้กับ submit score)
"""

import os

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/classroom.coursework.students",
    "https://www.googleapis.com/auth/classroom.rosters.readonly",
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]

# Project root = โฟลเดอร์ที่มี app.py อยู่ (อยู่สูงกว่า src/ หนึ่งระดับ)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CREDENTIALS_FILE = os.path.join(PROJECT_ROOT, "credentials.json")
TOKEN_FILE = os.path.join(PROJECT_ROOT, "token.json")


def get_credentials():
    """คืน Credentials ที่ valid; ถ้ายังไม่มี token ให้เปิดเบราว์เซอร์ให้ authorize ครั้งแรก"""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return creds


def get_classroom():
    """คืน Classroom API v1 client"""
    return build("classroom", "v1", credentials=get_credentials())


def get_id_token():
    """คืน id_token ล่าสุด (ใช้ยืนยันตัวตนกับ getscore1.com)"""
    creds = get_credentials()
    creds.refresh(Request())
    return creds.id_token