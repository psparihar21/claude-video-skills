// Shared motion for the Pushpstation gaming pack (v2). Deterministic: no clocks, no unseeded random.

// Slab markup: deep cover bar with violet/yellow/white accent bars leading and trailing it.
const SLAB = `
  <div class="bar y" style="left:3640px;width:150px"></div>
  <div class="bar v" style="left:3820px;width:300px"></div>
  <div class="bar w" style="left:4150px;width:36px"></div>
  <div class="bar d" style="left:0;width:3600px"></div>
  <div class="bar v" style="left:-280px;width:240px"></div>
  <div class="bar y" style="left:-400px;width:90px"></div>
  <div class="bar w" style="left:-450px;width:24px"></div>`;
function buildSlabs() {
  document.querySelectorAll(".slab").forEach((s) => (s.innerHTML = SLAB));
}
// slab sweeps in until the frame is fully covered (frame covered from at+dur)
function slabIn(tl, sel, at, dur = 0.42) {
  tl.fromTo(sel, { x: -4300 }, { x: 0, duration: dur, ease: "power3.out" }, at);
  tl.fromTo(`${sel} .bar:nth-child(-n+3)`, { x: -260 }, { x: 0, duration: dur + 0.12, ease: "power2.out", stagger: 0.03 }, at);
}
// slab carries on through and off the frame
function slabOut(tl, sel, at, dur = 0.42) {
  tl.to(sel, { x: 4300, duration: dur, ease: "power2.inOut" }, at);
  tl.to(`${sel} .bar:nth-child(n+5)`, { x: -200, duration: dur, ease: "power2.in", stagger: 0.03 }, at);
}
// wrap each letter in a mask so it can rise into place
function splitChars(sel) {
  document.querySelectorAll(sel).forEach((el) => {
    const t = el.textContent;
    el.innerHTML = [...t].map((c) => (c === " " ? " " : `<span class="mask"><span class="ch">${c}</span></span>`)).join("");
  });
}
function charsIn(tl, sel, at, each = 0.028) {
  tl.fromTo(`${sel} .ch`, { yPercent: 110 }, { yPercent: 0, duration: 0.42, ease: "power4.out", stagger: each }, at);
}
function charsOut(tl, sel, at) {
  tl.to(`${sel} .ch`, { yPercent: -110, duration: 0.24, ease: "power2.in", stagger: 0.012 }, at);
}
// a chip that grows from its left edge, then its label slides in
function chipIn(tl, sel, at) {
  tl.fromTo(sel, { scaleX: 0, skewX: -14, transformOrigin: "0% 50%" }, { scaleX: 1, skewX: -14, duration: 0.32, ease: "power4.out" }, at);
  tl.fromTo(`${sel} > span`, { x: -40, skewX: 14, opacity: 0 }, { x: 0, skewX: 14, opacity: 1, duration: 0.3, ease: "power3.out" }, at + 0.12);
}
function shine(tl, sel, at, width) {
  tl.fromTo(sel, { x: -200, skewX: -22 }, { x: width + 200, skewX: -22, duration: 0.6, ease: "power2.inOut" }, at);
}
// shrink a one-line text until it fits maxW (long game names)
function fit(sel, maxW) {
  const el = document.querySelector(sel);
  let fs = parseFloat(getComputedStyle(el).fontSize);
  while (el.scrollWidth > maxW && fs > 20) el.style.fontSize = (fs -= 2) + "px";
}
// YouTube-style subscribe click: pill -> cursor clicks -> SUBSCRIBED + bell ring. Markup from subscribeMarkup().
function subscribeMarkup() {
  return `<div class="sub-pill"><span class="sub-a">SUBSCRIBE</span><span class="sub-b">SUBSCRIBED</span></div>
  <div class="sub-bell"><svg viewBox="0 0 24 24" width="46" height="46"><path fill="#fff" d="M12 22a2.5 2.5 0 0 0 2.45-2h-4.9A2.5 2.5 0 0 0 12 22zm7-6V11a7 7 0 0 0-5.5-6.84V3.5a1.5 1.5 0 0 0-3 0v.66A7 7 0 0 0 5 11v5l-2 2v1h18v-1z"/></svg></div>
  <svg class="sub-cursor" viewBox="0 0 24 24" width="64" height="64"><path fill="#fff" stroke="#0B0820" stroke-width="1.4" d="M4 2l14 11-6 1 4 7-3 1.5-4-7-5 4z"/></svg>`;
}
function subscribeAnim(tl, root, at) {
  const q = (s) => `${root} ${s}`;
  tl.fromTo(q(".sub-pill"), { y: 140, scaleX: 0.3, opacity: 0 }, { y: 0, scaleX: 1, opacity: 1, duration: 0.45, ease: "back.out(1.6)" }, at);
  tl.fromTo(q(".sub-a"), { scale: 0.4, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.3, ease: "back.out(2)" }, at + 0.25);
  tl.fromTo(q(".sub-cursor"), { x: 260, y: 160, opacity: 0 }, { x: 0, y: 0, opacity: 1, duration: 0.55, ease: "power3.out" }, at + 0.6);
  tl.to(q(".sub-cursor"), { scale: 0.82, duration: 0.08, yoyo: true, repeat: 1 }, at + 1.2);
  tl.to(q(".sub-pill"), { scale: 0.93, duration: 0.08, yoyo: true, repeat: 1 }, at + 1.2);
  tl.set(q(".sub-pill"), { backgroundColor: "#2E2A45" }, at + 1.28);
  tl.set(q(".sub-a"), { opacity: 0 }, at + 1.28);
  tl.set(q(".sub-b"), { opacity: 1 }, at + 1.28);
  tl.fromTo(q(".sub-bell"), { scale: 0 }, { scale: 1, duration: 0.35, ease: "back.out(2.5)" }, at + 1.45);
  tl.to(q(".sub-cursor"), { x: 250, y: 6, duration: 0.4, ease: "power2.inOut" }, at + 1.55);
  tl.to(q(".sub-cursor"), { scale: 0.82, duration: 0.08, yoyo: true, repeat: 1 }, at + 2.0);
  tl.fromTo(q(".sub-bell svg"), { rotation: 0 }, { keyframes: [{ rotation: 22 }, { rotation: -20 }, { rotation: 14 }, { rotation: -8 }, { rotation: 0 }], duration: 0.7, ease: "none", transformOrigin: "50% 10%" }, at + 2.05);
}
