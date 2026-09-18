# TA-Classroom — คู่มือการตั้งค่า / คอนฟิก (HOW TO CONFIG)

เอกสารนี้รวมทุกอย่างที่ต้องรู้ในการ **ตั้งค่าโปรเจกต์, หา ID/ค่า API, และทำความเข้าใจระบบให้คะแนน** ครอบคลุมตั้งแต่ Google Classroom API → ระบบคะแนนเว็บ getscore1.com → ฟีเจอร์ให้คะแนนของแอป

---

## 1. ภาพรวมโปรเจกต์ทำงานยังไง

```
   Google Classroom (มีงาน/การส่งงานของนักศึกษา)
        │  Google Classroom API (OAuth 2.0)
        ▼
   TA-Classroom (Flask web app)  ── ดูคอร์ส/งาน/การส่งงาน
        │
        ├─ เปิดคลาสรูม   → ผู้ใช้ให้คะแนนเองบนหน้า Google Classroom
        │
        └─ ให้คะแนนเว็บ  ── URL + hash data (#classid/..) ──► getscore1.com
             (ปุ่ม ให้คะแนน / ให้คะแนนทุกคน)
                 │  Extension หรือ Bookmarklet
                 ▼
             getscore1.com/ta_score.php  → กรอกฟอร์ม + ส่งคะแนนอัตโนมัติ (POST JSON ผ่าน JS ของเว็บ)
```

จุดสำคัญ: **แอปเราไม่สามารถ POST คะแนนไป getscore1.com ตรงๆ ผ่าน backend ได้** เพราะเว็บเขา
ตรวจ `id_token` ของ Google (ออกให้เฉพาะหน้าเว็บของเขาเท่านั้น) + ไม่มี CORS → ต้องให้คะแนนผ่าน
การรันโค้ดบนหน้าเว็บเขา (extension / bookmarklet)

---

## 2. โครงสร้างโปรเจกต์

```
TA-Classroom/
├── app.py                  # Flask: routes + logic การให้คะแนน
├── requirements.txt        # pip dependencies
├── .env                    # sensitive config (ถูก .gitignore — ห้ามขึ้น git)
├── .env.example            # ตัวอย่างตัวแปร
├── README.md               # คู่มือติดตั้ง/ใช้งานหลัก
├── DESIGN.md               # spec หน้า UI
├── credentials.json        # [git-ignored] OAuth client ของเรา
├── token.json              # [git-ignored] token ที่ได้จาก authorize ครั้งแรก
├── extension/              # Chrome/Edge extension "TA Class Autofill"
│   ├── manifest.json
│   └── content.js          # auto-fill + submit บน getscore1
├── src/
│   ├── ta_auth.py          # OAuth: get_classroom() / get_credentials()
│   ├── check_courses.py    # CLI: รายชื่อคอร์ส
│   ├── check_coursework.py # CLI: รายชื่องาน (ค่าเริ่มต้น COURSE_ID=855107375121)
│   ├── fetch_submissions.py# CLI: ดึงการส่งงาน -> submissions.txt
│   └── check_token.py      # CLI: ดู scope/token
└── templates/              # Jinja2 templates (server-rendered)
```

---

## 3. การติดตั้งเบื้องต้น

```powershell
cd TA-Classroom
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

คัดลอก `.env.example` → `.env` แล้วใส่ค่าจริง (ดูหัวข้อ 4)

---

## 4. ตัวแปรระบบ (`.env`)

| ตัวแปร | ค่าเริ่มต้นในโค้ด | ใช้ทำอะไร |
|--------|------------------|-----------|
| `SECRET_KEY` | `ta-classroom-secret` | Flask sign session ควรเป็น random ยาวๆ |
| `CLASS_ID` | `2569CP412703` | `classid` ของ getscore1 ที่ตีงด้วยปุ่ม ให้คะแนนเว็บ |
| `WEB_GRADE_COURSES` | `855107375121,855274641019,855273686370` | `course_id` (คั่น comma) ที่ "ให้คะแนนเว็บ"/"ให้คะแนนทุกคน" ใช้ได้ — **วิชานอกนี้ดูได้แค่งาน** (ยังเปิดคลาสรูมได้) |

เปิด app:

```powershell
python app.py
# แล้วไป http://localhost:5000
```

วิธีหา api การเรียกใช้ตัวแปรเพิ่มเติม: ดู `.env.example` และ `app.py` บรรทัด top (~L15-30)

---

## 5. Google Classroom API — การตั้งค่า + "หา API เจอได้ที่ไหน"

### 5.1 สร้าง/เปิดใช้ API
1. เข้า **Google Cloud Console**: <https://console.cloud.google.com/>
2. เลือกโปรเจกต์ (หรือสร้างใหม่)
3. **APIs & Services → Library** → ค้นหา **Google Classroom API** → **Enable**
4. **APIs & Services → Enabled APIs & services** → ต้องเห็น `Google Classroom API`

### 5.2 สร้าง OAuth Client (Desktop app)
1. **APIs & Services → OAuth consent screen** → External → เพิ่มอีเมล TA เป็น **Test users**
2. **APIs & Services → Credentials → Create credentials → OAuth client ID**
   - Application type: **Desktop app**
   - ตั้งชื่ออะไรก็ได้ → Create
3. กด **Download JSON** → เอาไฟล์มาเก็บที่ root โปรเจกต์ ตั้งชื่อเป็น `credentials.json`

### 5.3 `token.json`
รันสักครั้ง เช่น:

```powershell
python src/check_courses.py
```

เบราว์เซอร์จะเปิดหน้า consent ให้ล็อกอินด้วยบัญชี TA → ยอมรับ → แอปสร้าง `token.json` (จะถูกนำไปใช้โดยอัตโนมัติทุกครั้งที่รัน) ถ้าจะ authorize ใหม่ (เช่น เปลี่ยนบัญชี) → **ลบ `token.json` แล้วรันใหม่**

### 5.4 Scope ที่ใช้ (อยู่ใน `src/ta_auth.py`)
```python
SCOPES = [
  classroom.coursework.students,  # ให้คะแนน/อ่านงาน+การส่ง
  classroom.rosters.readonly,     # อ่านรายชื่อนักศึกษา
  classroom.courses.readonly,     # อ่านรายวิชา
  userinfo.email, openid,         # สำหรับข้อมูลผู้ใช้
]
```

---

## 6. หา Course ID (รหัสวิชา) และ Coursework ID (รหัสงาน)

### 6.1 Course ID — มี 3 วิธี
1. **ในแอป**: เปิดหน้า `/courses` → URL ลิงก์จะเป็น `/coursework?course_id=<ID>`
2. **CLI**: `python src/check_courses.py` (โชว์ id + ชื่อวิชา)
3. **Google Classroom URL**: เปิดหน้าวิชา → ลิงก์ตรงแถบที่อยู่จะมี `classroom.google.com/c/<courseId>`

### 6.2 Coursework ID — มี 3 วิธี
1. **ในแอป**: ไป `/coursework?course_id=<ID>`
2. **CLI**: `python src/check_coursework.py` (ค่าเริ่มต้น COURSE_ID=855107375121 ดู ../top ของไฟล์)
3. **Google Classroom URL**: เปิดงาน → `classroom.google.com/c/<courseId>/a/<courseworkId>`

> ใช้ combo `course_id + coursework_id` ไปที่หน้า `/submissions?course_id=..&coursework_id=..`

### 6.3 กรอก ID ยังไงในแอป
จากหน้า `/submissions` เลือกวิชา (dropdown) → เลือกแลป (dropdown) — แอปจะ build URL ให้เอง ไม่ต้องพิมพ์ ID มือ

---

## 7. ระบบคะแนนเว็บ getscore1.com — กลไกที่ต้องรู้

### 7.1 มันคุยกันด้วย JSON (ไม่ใช่ฟอร์ม HTML)

POST → `https://getscore1.com/ta_score.php` (Content-Type: application/json)

```jsonc
// action แยกเป็น 3 แบบ
{ "action": "courses",  "id_token": "<Google ID token>" }
{ "action": "exercises","id_token": "...", "classid": "2569CP412703" }
{ "action": "submit",   "id_token": "...", "classid": "...",
  "exercise_id": "8", "last4": "5184", "score": "1" }
```

- **`id_token`** เป็น Google ID token ของ **GSI Client id:** `903997740631-jkoj2fe0m95knbme5ndrhkdcfrnuol3i.apps.googleusercontent.com`
  (มาจากปุ่ม Google Sign-In **บนหน้า getscore1 เท่านั้น** — backend ส่ง id_token ของ client เราไปไม่ได้ผล `auth:false`)
- Response `submit`: `{ ok, message, status: "saved"|"updated"|"dup", last4, name, score }`
- ถ้า token หมดอายุ/ใช้ไม่ได้ → `{ ok:false, auth:false }`
- **ไม่มี CORS** + ไม่โหลดฟอร์ม urlencoded → ทางเดียวที่จะส่งสำเร็จต้องรัน JS บนหน้าเขา (ดูข้อ 8)

### 7.2 หา classic ของ getscore1
ล็อกอินหน้า `ta_score.php` → เปิด DevTools (F12) → Console รัน:

```js
fetch('ta_score.php', {method:'POST', headers:{'Content-Type':'application/json'},
  body: JSON.stringify({action:'courses', id_token: 'PASTE_AN_ID_TOKEN'})}).then(r=>r.json()).then(console.log)
```

หรือดูแบบชิวๆ: ล็อกอิน แล้ว inspect `#courseSel` — `option.value` = `classid` ของแต่ละวิชา

### 7.3 หา exercise_id + คะแนนเต็มของแลป
ล็อกอิน → เลือกวิชา → inspect `#exSel`:
- `option.value` = `exercise_id` (ตัวเลขที่ใช้ในลิงก์)
- `option.dataset.max` (attribute `data-max`) = `max_score`

นำค่ามาใส่ใน `EXERCISE_MAP` (ข้อ 7.4)

### 7.4 `EXERCISE_MAP` ใน `app.py`

```python
EXERCISE_MAP = {
    "lab01": {"id": "8",  "max": 1},   # key labXX มาจากชื่อ work ใน Classroom
    "lab04": {"id": "19", "max": 4},
    # ... lab10: id 48, max 1
}
```

- **key** (`lab01`) ต้องตรงกับ pattern ใน **ชื่อ assignment** บน Classroom (regex `lab\s*0?(\d+)`) — ถ้าเปลี่ยนชื่อแลปใน Classroom ต้องแก้ตรงนี้ไปด้วย
- **id** = `exercise_id` ของ getscore1 (หาจากข้อ 7.3)
- **max** = คะแนนเต็ม ใช้ทั้งตรวจสอบขอบเขตคะแนน และเป็นค่า default ตอนให้คะแนน
- เพิ่มแลปใหม่แค่เพิ่ม dict เข้าไป + ตั้งชื่อ assignment เป็น `LabXX ...`

---

## 8. วิธีให้คะแนน 3 แบบ (ในหน้า /submissions)

| วิธี | ใช้เมื่อ | ต้องมีอะไร |
|------|---------|-----------|
| **เปิดคลาสรูม** | ต้องการดูงาน + ให้คะแนนด้วยตัวเองใน Google Classroom | ลิงก์ `alternateLink` ของงาน (อัตโนมัติ) — ใช้ได้ทุกวิชา |
| **ให้คะแนนเว็บ** (ทีละคน) | วิชาใน `WEB_GRADE_COURSES` เท่านั้น | Extension (แนะนำ) หรือ Bookmarklet |
| **ให้คะแนนทุกคน** (bulk) | วิชาใน `WEB_GRADE_COURSES` เท่านั้น | **ต้องติดตั้ง Extension ก่อน** (เลยต้องรอ confirm จาก extension ทีละคน) |

### 8.1 ข้อมูลใน URL (hash) ที่ส่งให้เว็บให้คะแนน
```
https://getscore1.com/ta_score.php#classid=2569CP412703&exercise_id=8&last4=5184&score=1
```
- `classid` = จาก `CLASS_ID` (env) — เปลี่ยนตรง `.env`
- `exercise_id` + คะแนนเต็ม = จาก `EXERCISE_MAP`
- `last4` = 4 ตัวท้ายรหัสนักศึกษา (หาได้จากชื่อไฟล์ — ข้อ 9)

### 8.2 Extension — auto-fill แบบไม่ต้อง bookmark (แนะนำ)
- โหลดครั้งเดียว: หน้า `/bookmarklet` → ดาวน์โหลด `manifest.json` + `content.js` → โฟลเดอร์ `ta-autofill/` → `chrome://extensions` → โหมด Developer → **Load unpacked**
- หลังแก้ `content.js` → กด refresh 🔄 ที่การ์ด extension (มันไม่ reload ไฟล์ให้เอง)
- extension อ่าน hash แล้วกรอก+ส่งบนหน้า getscore1, **ไม่ปิด tab** (ล็อกอินค้าง ทั้งช่วยให้คนถัดไปเร็วขึ้น + ไม่ต้องล็อกอินใหม่) แล้ว `postMessage` แจ้งหน้าแอป + `opener.focus()` กลับหน้า submissions

### 8.3 Whitelist วิชาที่ให้คะแนนเว็บได้
```dotenv
WEB_GRADE_COURSES=855107375121,855274641019,855273686370
```
ถ้าจะให้วิชาใหม่ใช้คะแนนเว็บได้ → เพิ่ม course_id ต่อท้าย (คั่นด้วย `,`) วิชานอกลิสต์: เห็น**แค่ดูงาน** + ปุ่มเปิดคลาสรูม (ไม่เห็น ให้คะแนนเว็บ / ให้คะแนนทุกคน)

---

## 9. `last4` — กติการหาชื่อไฟล์

แอปดึงรหัสนักศึกษาจาก **ชื่อไฟล์** ที่นักศึกษาส่ง (ดู `extract_last4` ใน `app.py`):

- ต้องขึ้นต้นด้วย `65|66|67|68` แล้วตามด้วยเลข รวม 9-10 หลัก (เช่น `663380518-4`, `663380518`)
- regex: `(?<!\d)(?:6[5-8]\d{8}|6[5-8]\d{7}(?:[-_]\d)?)(?!\d)`
- `last4` = **4 ตัวท้าย** ของรหัสนักศึกษา

ตัวอย่าง:
| ชื่อไฟล์ | last4 |
|----------|-------|
| `Lab01_663380518-4_นาย ก.ipynb` | `5184` |
| `Lab01_663380518_นาย ก.ipynb` | `0518` |
| `MyHomework.ipynb` | `None` → ไม่ได้ให้คะแนนเว็บ/ทุกคน (ขึ้นป้าย "ชื่อไฟล์ผิดรูปแบบ") |

> ถ้านักศึกษาส่งโดยไม่ตั้งชื่อตามแบบนี้ → ข้าม + แจ้งใน noti ("ยังไม่ได้ถูกให้คะแนน")

---

## 10. Troubleshooting

| อาการ | สาเหตุ / วิธีแก้ |
|-------|------------------|
| `Error 403: access_denied` ตอน authorize | ยังไม่ enable Classroom API หรือไม่ได้ล็อกอินด้วยบัญชีที่ใช่ |
| `Error 403: public client` / `redirect_uri_mismatch` | OAuth client ผิดประเภท — ต้องเป็น **Desktop app** |
| หน้า consent ไม่มีให้เลือกรับ | อีเมลไม่เป็น **Test user** ใน OAuth consent screen |
| "ให้คะแนนเว็บ" ไม่ทำงาน / autofill ไม่ขึ้น | extension เป็นเวอร์ชันเก่า → reload ที่ `chrome://extensions` (อาจต้องปิด tab getscore1 เดิมทิ้ง) |
| กด TA Autofill แล้วบอก "ลิงก์ไม่ครบ" | เปิดหน้า getscore1 มาเองเฉยๆ (ไม่มี hash) — ต้องกดผ่านปุ่ม ให้คะแนนเว็บ |
| ต้องล็อกอิน getscore1 ทุกคน | tab getscore1 ถูกปิด/ปัด — ให้ปล่อย tab ไว้ แล้วล็อกอินแค่ครั้งแรก |
| `auth:false` / session หมด | ล็อกอิน Google บนหน้า getscore1 ใหม่ (token id ~1 ชม.) |
| แลปไม่ขึ้นปุ่มให้คะแนนเว็บ | ชื่อ assignment ไม่ตรง `Lab##` หรือยังไม่เข้า `EXERCISE_MAP` |
| วิชาไม่เห็นปุ่มเว็บ | วิชานั้นไม่อยู่ใน `WEB_GRADE_COURSES` |
| API ติดขัด 429/5xx | Google quota/ชั่วคราว — แอปมี retry อัตโนมัติ 3 ครั้ง |
| backlink โดนประวิงโดย Classroom | ลิงก์งานเป็น `alternateLink` บางครั้งเปิดได้ครั้งเดียว — กด เปิดคลาสรูม ใหม่ |

---

## 11. CLI scripts (ใช้เทสต์ API เร็วๆ)

```powershell
python src/check_token.py        # ดู scope ว่า token ใช้ได้ไหม
python src/check_courses.py      # รายชื่อคอร์สทั้งหมด
python src/check_coursework.py   # งานของ COURSE_ID (แก้เลขในไฟล์ได้)
python src/fetch_submissions.py  # ดึง submission -> submissions.txt
```

---

## 12. ควรอ่านต่อ

- `README.md` — การติดตั้งหลัก + OAuth step-by-step
- `DESIGN.md` — spec หน้าตา UI
- `extension/content.js` + `BOOKMARKLET_SCRIPT` ใน `app.py` — contract การ autofill ที่ใช้จริง
- HTML ของ `ta_score.php` — ดู form/API ของ getscore1 จริง (ตรงนี้เป็นคนละระบบ ต้องไป inspect จากเว็บเอง)