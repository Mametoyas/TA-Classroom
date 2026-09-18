# TA Classroom

เครื่องมือช่วยงาน TA (Teaching Assistant) สำหรับ Google Classroom:

- ดูรายชื่อคอร์ส / งาน / การส่งงานของนักศึกษา
- Web UI (Flask) สำหรับดูและตรวจการส่งงาน
- CLI scripts สำหรับดึงข้อมูลอย่างรวดเร็ว
- ส่งคะแนนให้ระบบ `getscore1.com` (ผ่าน bookmarklet TA Autofill บนหน้าเว็บ)

## โครงสร้างโปรเจกต์

```
TA-Classroom/
├── app.py                     # Web app (Flask) — หน้า UI หลัก (อยู่ root)
├── src/                       # โค้ด Python หลัก
│   ├── __init__.py            # ทำให้ src เป็น package
│   ├── ta_auth.py             # Shared helper: Google OAuth + Classroom API
│   ├── check_courses.py       # CLI: ดูรายชื่อคอร์ส
│   ├── check_coursework.py    # CLI: ดูรายการงานของคอร์ส
│   ├── fetch_submissions.py   # CLI: ดึงการส่งงาน -> submissions.txt
│   └── check_token.py         # CLI: ดู scopes ใน token.json
├── requirements.txt
├── templates/                 # HTML templates (Jinja2)
│   ├── base.html
│   ├── index.html
│   ├── courses.html
│   ├── coursework.html
│   ├── submissions.html
│   └── bookmarklet.html
├── credentials.json           # [ไม่ commit] OAuth client จาก Google
├── token.json                 # [ไม่ commit] token หลัง authorize แล้ว
└── DESIGN.md                  # สเปกดีไซน์ UI
```

### ตรรกะสำคัญ

| ไฟล์ | ใช้ทำอะไร |
|------|-----------|
| `src/ta_auth.py` | `get_credentials()` โหลด/สร้าง `token.json`, `get_classroom()` (path อ้างอิง root เสมอ ไม่ขึ้นกับ CWD) |
| `app.py` | Routes: `/` (หน้าแรก), `/courses`, `/coursework`, `/submissions`, `/bookmarklet` (ติดตั้ง TA Autofill) |
| `submissions` route | ดึงรายชื่อ student + submission ของงานนั้น, จับคู่ให้ scorer ผูกกับ `exercise_id` + `last4` |

---

## สิ่งที่ต้องมี

- Python 3.9+
- บัญชี Google ที่มีสิทธิ์เข้าถึง Google Classroom ที่ต้องการ (`2569CP412703` หรือ course_id อื่น)
- Internet (เรียก Google API)

---

## วิธีติดตั้ง (Install)

```bash
# 1. ไปที่โปรเจกต์
cd C:\Store\Script-Programming\TA-Classroom

# 2. (แนะนำ) สร้าง virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

# 3. ติดตั้ง dependencies
pip install -r requirements.txt
```

---

## ตั้งค่า Google OAuth (เอาครั้งเดียว แต่สำคัญ)

ต้องมี `credentials.json` ที่ได้จาก Google Cloud Console. ทำตามนี้:

### 1. เปิด Google Cloud Console

- ไปที่ https://console.cloud.google.com
- ล็อกอินด้วยบัญชี Google **อันเดียวกับบัญชี TA** ที่ใช้เข้าถึง Classroom
- สร้างโปรเจกต์ใหม่ (หรือใช้โปรเจกต์เดิม) ที่มุมบนซ้าย → **New Project** → ตั้งชื่อ เช่น `ta-classroom` → **Create**

### 2. Enable Google Classroom API

- ในเมนูซ้าย: **APIs & Services → Library**
- ค้นหา `Google Classroom API` → คลิกเข้าไป → กด **Enable**

> สิ่งนี้สำคัญมาก — ถ้ายังไม่ enable จะเจอ error `403 dailyLimitExceededUnreg` หรือ `access_denied`

### 3. ตั้งค่า OAuth Consent Screen

- เมนูซ้าย: **APIs & Services → OAuth consent screen**
- เลือก **User type = External** → **Create**
- กรอกข้อมูล:
  - App name: `TA Classroom`
  - User support email: อีเมลของเรา
  - Developer contact email: อีเมลของเรา
- กด **Save and Continue**
- หน้า **Scopes**: กด **Add or remove scopes** แล้วเพิ่ม:
  - `https://www.googleapis.com/auth/classroom.courses.readonly`
  - `https://www.googleapis.com/auth/classroom.coursework.students`
  - `https://www.googleapis.com/auth/classroom.rosters.readonly`
  - `openid`
  - `https://www.googleapis.com/auth/userinfo.email`
- กด **Save and Continue**
- หน้า **Test users**: เพิ่มอีเมลของเราเอง (และอีเมล TA ที่จะใช้งาน) ลงในรายการ
  - เพราะ app อยู่ในสถานะ **Testing** จะใช้ได้เฉพาะคนที่อยู่ในลิสต์นี้
- กด **Save and Continue** จนจบ

> ⚠️ ถ้าอยากให้คนอื่นใช้ได้โดยไม่ต้องเข้าลิสต์ test users ต้องเปลี่ยนสถานะเป็น **In production** ในหน้า OAuth consent screen

### 4. สร้าง OAuth Client ID (Desktop app)

- เมนูซ้าย: **APIs & Services → Credentials** → กด **+ Create Credentials** → **OAuth client ID**
- แบบ: **Desktop app**
- ชื่อ: `TA Classroom Desktop`
- กด **Create**
- จะได้ pop-up แสดง **Client ID / Client Secret** → กด **Download JSON** เพื่อดาวน์โหลดไฟล์

### 5. วางไฟล์ credentials.json

- ตั้งชื่อไฟล์ที่ดาวน์โหลดมาเป็น **`credentials.json`**
- วางไว้ในโฟลเดอร์นี้ (ข้าง `app.py`):
  ```
  TA-Classroom/
  └── credentials.json
  ```
- ไฟล์นี้คือ secret — มี `.gitignore` กันไม่ให้ commit ขึ้น git แล้ว ✅

### 6. รัน authorize ครั้งแรก

```bash
python src/check_courses.py
```

ครั้งแรกจะเปิดเบราว์เซอร์ให้ล็อกอิน Google และกด **Allow** แล้วระบบจะ:
- สร้างไฟล์ `token.json` อัตโนมัติ
- แสดงรายชื่อคอร์สทั้งหมด

> `token.json` เป็นไฟล์ authorized token — มีอายุ ~1 ชม. แต่ระบบ refresh อัตโนมัติจาก `refresh_token` ดังนั้นรันซ้ำไม่ต้อง authorize ใหม่

---

## วิธีรัน

### Web app (Flask)

```bash
python app.py
```

เปิด `http://localhost:5000` ในเบราว์เซอร์

| หน้า | URL | รายละเอียด |
|------|-----|-----------|
| หน้าแรก | `/` | เมนูหลัก |
| Courses | `/courses` | รายชื่อคอร์สทั้งหมด |
| Course Work | `/coursework?course_id=...` | รายการงานของคอร์ส |
| Submissions | `/submissions?course_id=...&coursework_id=...` | การส่งงาน + ส่งคะแนน |

**ส่งคะแนน:** หน้า submissions → กดปุ่ม **"ให้คะแนน"** แล้วเลือกได้ 2 อย่าง: **เปิดคลาสรูม** (เปิดงานนั้นเพื่อตรวจ/ให้คะแนนด้วยตัวเองบน Google Classroom) หรือ **ให้คะแนนเว็บ** (เปิด `getscore1.com/ta_score.php` พร้อมข้อมูลใน URL) — แล้วกด bookmarklet **TA Autofill** (ดู `/bookmarklet`) เพื่อกรอกและส่งคะแนนอัตโนมัติ คะแนนกรอกเองได้ (มี `max` ตามแลป), `last4` ดึงจากชื่อไฟล์อัตโนมัติ (ไฟล์ที่ไม่มีรหัสนักศึกษา ขึ้นต้น 65-68 จะมีป้ายเตือนบอกชื่อไฟล์)

> ⚠️ getscore1.com ยอมรับเฉพาะ session + `id_token` ของปุ่ม Google Sign-In บนเว็บของมันเอง ดังนั้นต้องล็อกอิน Google บนเว็บก่อน (ครั้งแรก) และการส่งคะแนนต้องทำผ่านหน้าเว็บนั้น (bookmarklet) — backend ส่งตรงไม่สามารถทำได้ (`auth: false`)

### CLI scripts

```bash
# ดูคอร์สทั้งหมด
python src/check_courses.py

# ดูงานของคอร์ส (course_id default = 855107375121)
python src/check_coursework.py
python src/check_coursework.py <course_id>

# ดึงการส่งงานไปเป็น submissions.txt
python src/fetch_submissions.py
python src/fetch_submissions.py <course_id> <coursework_id>

# ดูว่า token มี scope อะไรบ้าง
python src/check_token.py
```

---

## ตั้งค่าผ่าน Environment Variables

| Variable | Default | ใช้ทำอะไร |
|----------|---------|-----------|
| `SECRET_KEY` | `ta-classroom-secret` | Flask secret key |
| `CLASS_ID` | `2569CP412703` | classid สำหรับส่งคะแนน getscore1 |
| `WEB_GRADE_COURSES` | `855107375121,855274641019,855273686370` | `course_id` (คั่นด้วย comma) ที่ให้ปุ่ม "ให้คะแนนเว็บ"/"ให้คะแนนทุกคน" — วิชาอื่นดูได้แค่งาน (ยังเปิดคลาสรูมได้) |

ค่าจริงควรใส่ในไฟล์ **`.env`** (root ของโปรเจกต์ — ถูก `.gitignore` แล้ว, แอปจะ `load_dotenv` ตอนสตาร์ท) โดยคัดลอกจาก `.env.example` แล้วใส่ค่าของตัวเอง ตัวอย่าง:

```dotenv
SECRET_KEY=random-ยาว-ๆ-ของคุณ
CLASS_ID=2569CP412703
WEB_GRADE_COURSES=855107375121,855274641019,855273686370
```

ถ้าต้องการ override ตอนรัน (env shell ชนะ `.env`):
```powershell
$env:SECRET_KEY = "something-secret"
$env:CLASS_ID = "2569CP412703"
python app.py
```

---

## Troubleshooting

| ปัญหา | สาเหตุ / วิธีแก้ |
|-------|-----------------|
| `Error 403: access_denied` ที่หน้า authorize | ไม่ได้ enable Classroom API หรืออยู่หน้า consent ไม่ถูกต้อง — กลับไป step 2 |
| `Error 403: public client` / `redirect_uri_mismatch` | ใช้ OAuth client ผิดประเภท — ต้องเป็น **Desktop app** ไม่ใช่ Web |
| `'Client is unauthorized'` /  blocked | อีเมลไม่ถูกเพิ่มเป็น **Test user** — กลับไป step 3 |
| เจอ token.json แต่ใช้ไม่ได้ | ลบ `token.json` แล้วรัน `python src/check_courses.py` อีกครั้ง |
| กด "ให้คะแนนเว็บ" แล้วเว็บขึ้น "เซสชันหมดอายุ" | ต้องล็อกอิน Google บนหน้า getscore1.com ก่อน (ครั้งแรก/เมื่อเซสชันหมด) และใช้ bookmarklet **TA Autofill** กรอก/ส่งแทนการ POST ผ่าน backend |
| โดน rate limit เรียก API ถี่ไป | Google Classroom API มี quota 1,000 req/นาที/โปรเจกต์ — กันไว้ตรวจสอบแล้ว |

### วิธีลบ token แล้ว authorize ใหม่

```bash
del token.json        # Windows
# rm token.json       # macOS / Linux

python src/check_courses.py   # เปิด browser ให้ authorize ใหม่
```

---

## License / หมายเหตุ

- ใช้เพื่อการบริหารจัดการห้องเรียนเท่านั้น
- `credentials.json` และ `token.json` ต้องเก็บเป็นความลับ — ห้าม commit ขึ้น git