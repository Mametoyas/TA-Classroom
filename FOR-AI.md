# TA-Classroom — คู่มือทำความเข้าใจโค้ดทั้งโปรเจกต์ (อ่านก่อนแก้ไข)

> เอกสารนี้คือ "ไฟล์ที่ AI / คนใหม่ ต้องอ่านก่อนแตะโค้ด" — ครอบคลุมสถาปัตยกรรม, data flow,
> จุดที่แก้บ่อย, และกับดักที่ทำให้แอปพังถ้าไม่รู้ ต่างจาก `README.md` (วิธีติดตั้ง),
> `HOW-TO-CONFIG.md` (การตั้งค่าคอนฟิก), `DESIGN.md` (สเปกหน้าตา UI) — อันนี้คือ **อ่านโค้ดให้เข้าใจ**

---

## 1. โปรเจกต์นี้คืออะไร (สรุป 1 นาที)

เครื่องมือช่วยงาน TA ของวิชาเรียน CP412703: **อ่านข้อมูลจาก Google Classroom API แล้วแสดงเป็นเว็บ UI**
(Fast, ดูคอร์ส/งาน/การส่งงาน) และนำต่อกับ **ระบบให้คะแนนเว็บ `getscore1.com`** เพื่อส่งคะแนนให้
นักศึกษาแบบอัตโนมัติ (ทีละคน หรือทั้งชั้น)

แบ่งเป็น 3 ส่วนหลัก:

1. **Backend** — `app.py` (Flask, ไฟล์เดียว) + `src/` (shared OAuth helper + CLI scripts)
2. **Frontend** — ผิว Flask render template (Jinja2) ใน `templates/` ไม่มี framework ไม่มี build step
3. **Browser automation** — `extension/` (Chrome/Edge MV3) + bookmarklet (`BOOKMARKLET_SCRIPT` ใน app.py)
   เอาไว้กรอก/ส่งคะแนนอัตโนมัติบนหน้า `getscore1.com/ta_score.php`

**หัวใจสำคัญของทั้งระบบ:** ตัวแอป **ส่งคะแนนตรง ๆ ไม่ได้** (อย่าพยายาม "แก้ให้ส่งได้")
เว็บ getscore1.com จะรับเฉพาะ `id_token` จากปุ่ม Google Sign-In **บนหน้าเว็บของมันเองเท่านั้น**
ดังนั้นการให้คะแนนต้องเปิดหน้าเว็บนั้นขึ้นมา พร้อมข้อมูลผู้เรียนใส่ใน **URL hash**
แล้วให้ bookmarklet/extension กรอกฟอร์ม + กด submit แทนคุณ

---

## 2. ลำดับการอ่านไฟล์ (Read order)

กดอ่านตามนี้ ต่อกันได้จบเรื่อง:

1. `app.py` — entry point + ตรรกะหลักทั้งหมด (อ่านทั้งไฟล์จบได้ทีเดียว)
2. `src/ta_auth.py` — OAuth / วิธีได้ API client
3. `extension/content.js` — ฝั่ง browser automation (ส่วนที่ซับซ้อนสุดในแง่ timing)
4. `templates/submissions.html` — หน้าให้คะแนน (มี JS protocol ต่อกับ extension)
5. `templates/base.html` — แพทเทิร์น UI กลาง (CSS variable + sidebar + collapsible)
6. `src/` อื่น ๆ — CLI scripts สั้น ๆ อ่านง่าย
7. อ่านเอกสารประกอบ: `README.md`, `HOW-TO-CONFIG.md`, `DESIGN.md`

---

## 3. ภาพรวม Data Flow

```
   Google Classroom (API v1, OAuth 2.0 scope coursework/rosters/courses.readonly)
        │  get_classroom()  (src/ta_auth.py)
        ▼
   TA-Classroom Flask app (app.py)  ── หน้า /courses /coursework /submissions
        │
        ├─ "เปิดคลาสรูม"      → ผู้ใช้ให้คะแนนเองบน Google Classroom (patch assignedGrade + return)
        │
        └─ "ให้คะแนนเว็บ" / "ให้คะแนนทุกคน"   (เฉพาะวิชาใน WEB_GRADE_COURSES)
              │  เปิด window ชื่อ 'getscore_tab' พร้อม URL hash:
              │  https://getscore1.com/ta_score.php#classid=..&exercise_id=..&last4=..&score=..
              ▼
        browser ฝั่ง getscore1.com  ── extension/content.js หรือ bookmarklet กรอกฟอร์ม + submit
              │  เมื่อบันทึกสำเร็จ → postMessage({source:'ta-autofill', type:'done', last4}) กลับหน้าแอป
              ▼
        หน้า /submissions mark "ให้คะแนนแล้ว" (localStorage)
```

**ข้อบังคับ:** tab getscore1 จะเปิดค้างไว้ (window ชื่อ `getscore_tab`) เพื่อให้ Google login
อยู่ต่อ ใช้คนถัดไปได้โดยไม่ต้องล็อกอินใหม่ — **อย่าเปลี่ยนชื่อ window นั้น**

---

## 4. โครงสร้างไฟล์ + แต่ละไฟล์ทำอะไร

```
TA-Classroom/
├── app.py                     ★ แกนหลัก — Flask routes + mapping คะแนน + bookmarklet script
├── requirements.txt           deps: google-api-python-client, google-auth-*, flask, requests, python-dotenv
├── .env                       [git-ignored] SECRET_KEY / CLASS_ID / WEB_GRADE_COURSES
├── .env.example               ตัวอย่าง .env
├── credentials.json           [git-ignored] OAuth client (ดาวน์โหลดจาก Google Cloud)
├── token.json                 [git-ignored] token ที่ authorize แล้ว (auto-refresh, ลบ=re-auth)
├── submissions.txt            [git-ignored] ไฟล์ผลลัพธ์จาก CLI fetch_submissions
├── README.md                  วิธีติดตั้ง + OAuth step-by-step
├── HOW-TO-CONFIG.md           วิธีตั้งคอนฟิก / หา ID ต่าง ๆ / ระบบ getscore1
├── DESIGN.md                  spec หน้าตา UI (Material-ish)
├── FOR-AI.md                  ★ ไฟล์นี้ — อ่านโค้ดให้เข้าใจก่อนแก้
│
├── src/                       ใช้เป็น package (import "ta_auth" ได้)
│   ├── ta_auth.py             ★ SCOPES +  get_credentials() / get_classroom() / get_id_token()
│   ├── check_courses.py       CLI: list คอร์ส
│   ├── check_coursework.py    CLI: list งาน (COURSE_ID default 855107375121)
│   ├── fetch_submissions.py   CLI: ดึงการส่งงาน → submissions.txt
│   └── check_token.py         CLI: ดู scopes ใน token.json
│
├── templates/                 Jinja2 (server-rendered, ไม่มี JS framework)
│   ├── base.html              ★ shell กลาง: CSS variables, app bar, sidebar, collapsible
│   ├── index.html             หน้าแรก (เมนู)
│   ├── courses.html           รายชื่อคอร์ส
│   ├── coursework.html        รายการงานในคอร์ส
│   ├── submissions.html       ★ หน้าให้คะแนน (ล็อกการทำงานกับ extension อยู่ตรงนี้)
│   ├── bookmarklet.html       หน้าแนะนำติดตั้ง bookmarklet / extension
│   └── error.html             หน้า error จาก Google API
│
├── extension/                 ★ Chrome/Edge Extension "TA Class Autofill" (MV3) — ใช้แจกผ่าน Flask
│   ├── manifest.json          content_scripts: https://getscore1.com/ta_score.php*
│   └── content.js             อ่าน hash → กรอก → submit → postMessage กลับ
│
└── ta-autofill/               ★ โฟลเดอร์ COPY ของ extension/ (ดูกับดัก ข้อ 9.1)
    ├── manifest.json          ให้คนโหลดไปโหลดแบบ "Load unpacked" ด้วย folder นี้
    └── content.js             ต้อง sync กับ extension/content.js เสมอ
```

---

## 5. สี่อย่างที่ต้องเข้าใจก่อนแตะโค้ด

### 5.1 OAuth (src/ta_auth.py)

- `SCOPES` (L17-23): `classroom.coursework.students`, `classroom.rosters.readonly`,
  `classroom.courses.readonly`, `userinfo.email`, `openid`
- `PROJECT_ROOT` (L26) คำนวณจาก `__file__` → **โค้ดไม่ยึด CWD** รันจากที่ไหนก็ได้
- `get_credentials()` (L32): โหลด `token.json`; ถ้า expired + มี refresh_token → refresh เอง;
  ถ้าไม่มีไฟล์ → เปิด `InstalledAppFlow.run_local_server` (เบราว์เซอร์ขึ้นหน้า authorize ครั้งแรก) แล้วเขียน `token.json`
- `get_classroom()` (L48): เรียก `build("classroom", "v1", ...)`

### 5.2 EXERCISE_MAP — จับคู่ "แลปใน Classroom" กับ "exercise ใน getscore1" (app.py L62-73)

```python
EXERCISE_MAP = {
    "lab01": {"id": "8",  "max": 1},   # lab04 เป็น 4 คะแนน, ที่เหลือ 1
    ...
}
```

- **key** (`labXX`) ต้องตรงกับชื่อ assignment บน Classroom ผ่าน regex
  `lab\s*0?(\d+)` ใน `guess_exercise_id()` (app.py:129)
- **id** = `exercise_id` ของ getscore1 (ดูจาก option ของ `#exSel` บนเว็บ)
- **max** = คะแนนเต็ม — ใช้เป็น default หน้าให้คะแนน + ตรวจสอบขอบเขตคะแนน
- `EXERCISE_ID_TO_MAX` (app.py:76) เป็น reverse map สำหรับตรวจสอบคะแนน

### 5.3 WEB_GRADE_COURSES — วิชาที่ "ให้คะแนนเว็บ" ได้ (app.py L21-27)

- เป็น set ของ course_id (จาก env, default 3 วิชา)
- วิชานอกลิสต์: เห็น**แค่ดูงาน + เปิดคลาสรูม** ไม่มีปุ่ม "ให้คะแนนเว็บ" / "ให้คะแนนทุกคน"
- เช็คที่ `can_web_grade = course_id in WEB_GRADE_COURSES` (app.py:253)

### 5.4 Hash URL contract กับ getscore1.com

ทุกช่องทาง autofill ใช้ format เดียวกัน (สร้างใน `openWebGrade` submissions.html:346):

```
https://getscore1.com/ta_score.php#classid=2569CP412703&exercise_id=8&last4=5184&score=1
```

Field: `classid` (จาก `CLASS_ID` env) · `exercise_id` (จาก EXERCISE_MAP) · `last4`
(4 ตัวท้ายรหัสจากชื่อไฟล์) · `score` (ค่าที่กรอก)

---

## 6. ระบบให้คะแนน 3 วิธี (ปุ่มในหน้า Submissions)

| ปุ่ม | ฝั่งที่ลงมือ | โค้ดที่เกี่ยวข้อง |
|-----|-------------|-------------------|
| เปิดคลาสรูม | ตัวผู้ใช้เองบน Google Classroom | ลิงก์ `alternateLink` ของงาน (submissions.html:257) |
| ให้คะแนนเว็บ (ทีละคน) | bookmarklet / extension บน getscore1 | `openWebGrade()` submissions.html:337 |
| ให้คะแนนทุกคน (bulk) | extension เท่านั้น (ต้องติดตั้ง) | `gradeAll()` submissions.html:461 |

### 6.1 ข้อมูลที่หน้า Submissions ใช้

`/submissions` route (app.py:177) ดึงของจาก Classroom API หลายรายการในหน้าเดียว:
`courses.list` + `courseWork.list` + (ถ้าเลือกงานแล้ว) `courseWork.get` + `students.list`
+ `studentSubmissions.list` — ทุกตัวเรียกผ่าน `_api_call()` (app.py:32) ซึ่งมี retry 3 ครั้ง
เฉพาะ HTTP 429/5xx แบบ exponential backoff

ต่อ submission สร้าง entry ที่มี: state, badge (จาก `STATE_LABEL` app.py:106), ชื่อ, รายชื่อไฟล์,
`last4` (จาก `extract_last4` app.py:114), `exercise_id`/`max_points` (จาก `guess_exercise_id`),
`classroom_link` และจับกลุ่มด้วย `grouped[(state, label, badge)]`

สำหรับปุ่ม "ให้คะแนนทุกคน" ฝั่ง template รับ `grade_items` (TURNED_IN + มี exercise_id + มี last4)
กับ `grade_skipped` (TURNED_IN + ไม่มี last4 → ข้ามแล้วแจ้งใน noti)

### 6.2 วิธี "เปิดคลาสรูม" ผ่าน backend จริง ๆ (app.py `grade_classroom` L292)

ถ้าเทียบกับ "ให้คะแนนเว็บ" แล้วยังมีอีกทางที่ backend ทำได้จริง: POST ไป `/grade_classroom`
→ ตรวจคะแนน 0..max → `patch` `assignedGrade`+`draftGrade` → `return_` (ส่งคืนให้นักศึกษาเห็นคะแนน)
→ `jsonify({ok:true})`. (กำลังใช้จาก UI จริงหรือยัง — เป็นเส้นทางที่ออกแบบไว้แล้ว อย่าลบ)

### 6.3 วิธี "ให้คะแนนเว็บ" (ทีละคน)

`openWebGrade()` (submissions.html:337):
1. clamp คะแนน 0..max (`clampScore`)
2. ถ้าไม่มี `last4` → alert + กลับ (ชื่อไฟล์ผิดรูปแบบ)
3. `window.open(url, 'getscore_tab')` เปิด/ยึด tab เดิม → `win.blur()` + `window.focus()`
4. mark graded ใน localStorage + เปลี่ยนปุ่มเป็น "ให้คะแนนแล้ว"

จากนั้น browser ฝั่ง getscore1 ทำต่อ (ใครก็ได้คนหนึ่งที่ติดตั้ง — extension หรือ bookmarklet)

### 6.4 วิธี "ให้คะแนนทุกคน" (bulk)

`gradeAll()` (submissions.html:461):
- วน `GRADE_ITEMS` ทีละคน เปิด `window.open(url, 'getscore_tab')` (เปิดฉากหลัง)
- `waitSubmit(last4, timeout)` รอ **postMessage** ยืนยันจาก extension — คนแรก 60s (เผื่อล็อกอิน), คนถัดไป 30s
- ยืนยันแล้ว → `markRowGraded` / ไม่ยืนยัน → เก็บใน `failed` สรุปตอนจบ

**ใครเป็นคนยืนยัน:** extension `content.js` `finish()` (L45) หลัง submit สำเร็จ → `window.opener.postMessage({source:'ta-autofill', type:'done', last4,...}, '*')` + `window.opener.focus()`
หน้าแอปรับที่ listener (submissions.html:428) → เก็บใน `doneBuffer[last4]`

---

## 7. ฝั่ง browser automation (ส่วนละเอียดอ่อนที่สุด)

### 7.1 Bookmarklet กับ Extension ต่างกันยังไง

- **Bookmarklet** = JS `BOOKMARKLET_SCRIPT` ใน app.py:81 (string ยาวใน Python) —
  ผู้ใช้กดเองบนหน้า getscore1 หลังกด "ให้คะแนนเว็บ" → ไม่มี timing แทรกแซงจากเรานอกเหนือจากโค้ดตัวเดียว
- **Extension** = `extension/content.js` — รันอัตโนมัติ `run_at: document_idle` +
  ฟัง `hashchange` (L109) → กด "ให้คะแนนเว็บ" คนถัดไปใน tab เดียว ทำงานเองได้เลย
  มีฟีเจอร์พิเศษ: **postMessage ยืนยันความสำเร็จ** กลับหน้าแอป (bookmarklet ไม่มีอันนี้)

### 7.2 ลำดับขั้นของ extension (content.js)

`runAutofill()` (L84):
1. `parseParams()` อ่าน hash; ไม่มี `classid`/`exercise_id` → หยุด (อย่าไปยุ่งกับหน้า web อื่น)
2. `waitFor(isLoggedIn)` — `#appCard` ไม่มี class `hidden` + `#courseSel` มี option > 1
   (คือล็อกอิน Google แล้ว; ถ้าหมดเวลา 30s → warn)
3. ถ้า course/exercise ต่างจากที่อยู่ → `pick()` select + dispatch `change`
4. รอ `#exSel` โหลด → `pick` exercise → รอ `#score` มีค่า
5. `fillAndSubmit()` (L62): เซ็ต `#last4`/`#score` → `form.requestSubmit()`
6. รอ condition: `#submitBtn` active + `#status` แสดง + class เป็น `s-ok|s-info|s-warn`
   (8s) → `finish()` (L45): postMessage + focus กลับ (ไม่ปิด tab — กัน idToken หาย)

**DOM element IDs ที่ที่ใช้ (สมมุติจากหน้า getscore1 จริง):** `appCard`, `courseSel`, `exSel`,
`score`, `last4`, `scoreForm`, `submitBtn`, `status` — ถ้าเว็บ getscore1 เปลี่ยน HTML ต้องแก้ทั้ง
`content.js` และ `BOOKMARKLET_SCRIPT` พร้อมกัน (ดูกับดัก 9.2)

---

## 8. Frontend (templates)

- **base.html** — shell กลาง: CSS custom properties ตาม DESIGN.md (`--color-primary-blue` #1A73E8 ฯลฯ),
  app bar + sidebar nav + collapsible section (JS ใน base.html ท้ายไฟล์), แสดง breadcrumb ผ่าน
  `{% set breadcrumb = ... %}` ใน child template
- **แพทเทิร์นซ้ำ** ของแต่ละหน้า: `tab-bar` + `content-area` + `section-block` + `list-rows/list-row`
- หน้าใหม่ที่จะเพิ่ม: สร้าง template extends `base.html` + เพิ่ม nav item ใน sidebar (base.html) + route ใน app.py
- **สถานะ "ให้คะแนนแล้ว" เก็บฝั่ง browser เท่านั้น** (submissions.html L315):
  `STORAGE_KEY = 'graded_{coursework_id}'` ใน localStorage — ไม่มีข้อมูลอยู่ใน backend
  ปุ่ม reset (L401) ลบคีย์นี้แล้วคืนสไตล์ลิสต์

---

## 9. กับดัก — ถ้าไม่รู้แล้วแก้ พังชัวร์

### 9.1 `extension/` กับ `ta-autofill/` เป็น copy กัน (ต้อง sync ทั้งคู่) ⚠️

Flask แจกไฟล์จากโฟลเดอร์ `extension/` (route `/extension/<path>` app.py:171, bookmarklet.html:118)
แต่หน้าแนะนำให้ผู้ใช้โหลดไปวางในโฟลเดอร์ชื่อ `ta-autofill/` (มี folder `ta-autofill/` เก็บไว้ใน repo
เป็น convenience copy) ปัจจุบัน `content.js`/`manifest.json` ทั้ง 2 ที่**เหมือนกันทุกตัวอักษร**

**เวลาจะแก้ content.js → แก้ทั้ง 2 โฟลเดอร์** ไม่งั้นคนที่โหลดแล้วได้เวอร์ชันเก่า
(ตรงนี้ใช้เป็นโจทย์จับ error ของ AI บ่อย: "แก้ extension แล้วไม่เห็นผล" = แก้ที่เดียว)

### 9.2 Bookmarklet script กับ content.js เป็นคนละ implementation ที่ต้องตามกัน

`BOOKMARKLET_SCRIPT` (ใน app.py) กับ `extension/content.js` มี **contract เดียวกัน** (hash + DOM IDs)
แต่คนละโค้ด เปลี่ยน behavior ต้องแก้ทั้งคู่ (หรืออย่างน้อยให้ยังทำงานด้วยกันได้กับหน้า getscore1 เดิม)

### 9.3 `submit_score` (app.py:336) เป็น **deprecated ตั้งใจ** — อย่า "แก้ให้ทำงาน"

route นี้ return 501 เสมอ เพราะ **backend ส่งคะแนนไป getscore1 ไม่ได้จริง**:
`id_token` จาก OAuth client ของเราถูก getscore1 ตอบ `auth:false` วิธีเดียวที่เวิร์คคือรัน JS
บนหน้าเว็บเขา (bookmarklet/extension) → ถ้าเจอ "ควรจะส่งตรง ๆ ได้ที่" นี่คือกับดัก อย่าไปทำ

### 9.4 Regex สองตัวที่ผูกกับข้อมูลจริง (โลกภายนอก)

- `extract_last4` (app.py:114): `(?<!\d)(?:6[5-8]\d{8}|6[5-8]\d{7}(?:[-_]\d)?)(?!\d)`
  = รหัสนักศึกษา ขึ้นต้น 65-68 รวม 9-10 หลัก (แบบมี/ไม่มี `-x` ต่อท้าย) → last4 = 4 ตัวท้าย
- `guess_exercise_id` (app.py:129): `lab\s*0?(\d+)` → ต้องตรงกับชื่อ assignment บน Classroom

เปลี่ยนกติกาชื่อไฟล์/ชื่อแลปใน Google Classroom → จำต้องแก้ตรงนี้ (และ EXERCISE_MAP)

### 9.5 อย่าแตะ `'getscore_tab'` และไอเดีย "เปิด tab ค้างไว้"

window name `'getscore_tab'` (submissions.html:352,486) คือกลไกที่ทำให้ใช้ tab เดียววนทุกรอบ
→ เก็บ Google login ของ getscore1 ไว้ (idToken เป็น memory-only ของเว็บ) → ถ้าเปลี่ยนเป็นสุ่ม
หรือปิด tab หลัง submit จะบังคับให้ล็อกอินใหม่ทุกคน

### 9.6 Google API quota

หน้า `/submissions` เรียก API หลายตัวต่อ 1 request — API quota ~1,000 req/min (โฟลว์แบบ OAuth)
ถ้า features ใหม่จะเรียก API เพิ่ม ระวัง rate limit; `_api_call` จัดการ retry ให้เฉพาะ 429/5xx

### 9.7 OAuth state

- token อายุ ~1 ชม. แต่ refresh อัตโนมัติ (ถ้ามี refresh_token) — รันซ้ำได้ไม่ต้อง authorize
- เปลี่ยนบัญชี/scope → **ลบ `token.json`** แล้วรัน `python src/check_courses.py` ใหม่
- `credentials.json`/`token.json` มี `.gitignore` กันไว้แล้ว — อย่าลบออกจาก gitignore

### 9.8 HTML ฝั่ง getscore1 ไม่ใช่ของเรา

DOM ID (`appCard`, `courseSel`, ...) เป็น**สมมุติฐานจากหน้าเว็บจริง** ของจริงเปลี่ยนได้ทุกเมื่อ
เวลาแอป Autofill พัง อย่างแรกที่ควรทำ = เปิด DevTools หน้า ta_score.php ตรวจว่า ID ยังเหมือนเดิม

---

## 10. ตารางเมนูแก้ไขงานประจำ (Common Task → ไปแก้ที่ไหน)

| อยากทำ | ไปแก้ที่ |
|--------|---------|
| เพิ่มแลปใหม่ (เช่น Lab11) | เพิ่ม dict ใน `EXERCISE_MAP` (app.py:62) — id/max หามาได้จาก `#exSel` option + `data-max` บน getscore1 + ตั้งชื่อ assignment บน Classroom เป็น `Lab11 ...` |
| ให้วิชาใหม่ใช้คะแนนเว็บได้ | เพิ่ม course_id ใน `WEB_GRADE_COURSES` (`.env`) |
| เปลี่ยน classid (getscore1) | `CLASS_ID` ใน `.env` |
| เปลี่ยนกติกาชื่อไฟล์นักศึกษา | regex ใน `extract_last4` (app.py:114) |
| เปลี่ยน label/สีสถานะ | `STATE_LABEL` (app.py:106) + CSS `.chip-*` ใน base.html |
| เปลี่ยนหน้าตา UI | CSS vars ใน base.html (`:root`) + template ของหน้านั้น |
| เพิ่มหน้าเว็บใหม่ | route ใน app.py + template extends base.html + nav item ใน sidebar (base.html) |
| แก้ auto-fill (อินเทอร์เฟซกับ getscore1) | `extension/content.js` **+** `ta-autofill/content.js` **+** `BOOKMARKLET_SCRIPT` (app.py:81) — ดู 9.1/9.2 |
| เปลี่ยน endpoint/พฤติกรรม getscore1 | ต้องไป inspect หน้าเว็บจริงก่อน (คนละระบบ นอก repo) |

---

## 11. วิธีรัน / เช็กว่าโค้ดยังทำงาน

```powershell
pip install -r requirements.txt
python -m venv .venv        # แล้ว activate (ครั้งแรกเท่านั้น)
python src/check_courses.py # ถ้าไม่มี token.json จะเปิด browser authorize ครั้งแรก
python app.py               # แล้วเปิด http://localhost:5000
```

เส้นทาง UI ที่ใช้บ่อย:
- `/courses` → `/coursework?course_id=...` → `/submissions?course_id=...&coursework_id=...`
- `/bookmarklet` → หน้าแนะนำติดตั้ง bookmarklet + ดาวน์โหลด extension

CLI แบบเร็ว:
```powershell
python src/check_token.py        # scope ใน token.json
python src/check_coursework.py   # งานของ COURSE_ID (แก้เลขได้ในไฟล์/arg)
python src/fetch_submissions.py  # ดึง submission -> submissions.txt
```

> ไม่มี linter/test suite ในโปรเจกต์ (มีแค่ requirements) — วิธี "verify" คือรัน app แล้วเดิน
> flow: เปิด `/submissions` → เลือกวิชา/แลป → ล็อกอิน getscore1 → กด "ให้คะแนนเว็บ" →
> autofill ทำงาน + noti ขึ้นและปุ่มเปลี่ยนเป็น "ให้คะแนนแล้ว"