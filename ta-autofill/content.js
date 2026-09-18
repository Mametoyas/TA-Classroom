// TA Class Autofill — content script สำหรับ https://getscore1.com/ta_score.php
// อ่าน hash (#classid=..&exercise_id=..&last4=..&score=..) แล้วกรอกฟอร์ม + ส่งอัตโนมัติ
// รันซ้ำเมื่อ hash เปลี่ยน (กด "ให้คะแนนเว็บ" คนถัดไปใน tab เดียวกัน) โดยไม่ต้องรีโหลดหน้า

(function () {
  "use strict";

  var runId = 0;
  var TIMEOUT_MS = 30000;

  console.log("[TA Autofill] โหลดแล้ว v1.2 — รอ autofill จาก hash");

  function parseParams() {
    var p = {};
    (location.hash || "").replace(/^#/, "").split("&").forEach(function (kv) {
      var i = kv.indexOf("=");
      if (i > -1) p[kv.slice(0, i)] = decodeURIComponent(kv.slice(i + 1));
    });
    return p;
  }

  function waitFor(cond, cb, msLeft, id) {
    if (id !== runId) return;
    if (cond()) { cb(); return; }
    if (msLeft <= 0) { console.warn("[TA Autofill] หมดเวลา — ไม่พบข้อมูล/ไม่เข้าสู่ระบบ"); return; }
    setTimeout(function () { waitFor(cond, cb, msLeft - 200, id); }, 200);
  }

  function pick(sel, val, ev) {
    if (!sel) return;
    var found = false;
    for (var i = 0; i < sel.options.length; i++) {
      if (sel.options[i].value === val) { sel.selectedIndex = i; found = true; break; }
    }
    if (ev && found) sel.dispatchEvent(new Event("change"));
    return found;
  }

  function isLoggedIn() {
    var app = document.getElementById("appCard");
    var courseSel = document.getElementById("courseSel");
    return app && !app.classList.contains("hidden") && courseSel && courseSel.options.length > 1;
  }

  function finish(id) {
    if (id !== runId) return;
    console.log("[TA Autofill] บันทึกสำเร็จ — กลับหน้าแอปแล้ว (tab getscore1 ยังเปิดล็อกอินไว้ ใช้คนถัดไปได้เลย)");
    // โฟกัสกลับหน้าต้นทาง (/submissions) โดยไม่ปิด/ไม่ navigate tab นี้
    // ไม่งั้น idToken (memory-only ของเว็บ) จะหายและต้องล็อกอินใหม่ทุกคน
    var p = parseParams();
    if (window.opener) {
      try {
        window.opener.postMessage(
          { source: "ta-autofill", type: "done", last4: p.last4 || "", exercise_id: p.exercise_id || "" },
          "*"
        );
        window.opener.focus();
      } catch (e) { /* cross-origin ยัง postMessage/focus ได้ */ }
    }
  }

  function fillAndSubmit(id) {
    if (id !== runId) return;
    var p = parseParams();
    var last4 = document.getElementById("last4");
    var score = document.getElementById("score");
    var form = document.getElementById("scoreForm");
    if (!last4 || !score || !form) return;
    if (p.last4) last4.value = p.last4;
    if (p.score) score.value = p.score;
    if (form.requestSubmit) form.requestSubmit();
    else if (form.submit) form.submit();
    // รอจนกว่าจะบันทึกเสร็จจริง (submitBtn กลับมา active + สถานะสำเร็จ) แล้วกลับไปหน้าต้นทาง
    waitFor(function () {
      var btn = document.getElementById("submitBtn");
      var st = document.getElementById("status");
      return btn && !btn.disabled && st && st.style.display === "block" &&
        /(^|\s)(s-ok|s-info|s-warn)(\s|$)/.test(st.className);
    }, function () {
      setTimeout(function () { finish(id); }, 400);
    }, 8000, id);
  }

  function runAutofill() {
    var id = ++runId;
    var p = parseParams();
    if (!p.classid || !p.exercise_id) return; // ลิงก์ไม่ครบ — ไม่ไปยุ่งกับหน้า

    waitFor(isLoggedIn, function () {
      var courseSel = document.getElementById("courseSel");
      var exSel = document.getElementById("exSel");
      var same = courseSel.value === p.classid && exSel.value === p.exercise_id;

      if (same) { fillAndSubmit(id); return; }

      pick(courseSel, p.classid, true);
      waitFor(function () {
        return exSel && !exSel.disabled && exSel.options.length > 1;
      }, function () {
        pick(exSel, p.exercise_id, true);
        waitFor(function () {
          var s = document.getElementById("score");
          return s && s.value !== "";
        }, function () { fillAndSubmit(id); }, TIMEOUT_MS, id);
      }, TIMEOUT_MS, id);
    }, TIMEOUT_MS, id);
  }

  window.addEventListener("hashchange", runAutofill);
  runAutofill();
})();