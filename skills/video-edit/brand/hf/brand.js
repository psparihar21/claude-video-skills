// Shared motion for the Pushpstation pack (v4). Deterministic: every frame is computed from tween progress.
// The four controller shapes are the brand: triangle (volt), circle (coral), cross (sky), square (ink).

const SHAPE_COLOR = { triangle: "var(--color-volt)", circle: "var(--color-coral)", cross: "var(--color-sky)", square: "var(--color-ink)" };
// radius that covers a 1920x1080 or 1080x1920 frame from its centre, per shape
const COVER_R = { circle: 1160, square: 1700, triangle: 2400, cross: 4200 };

// polygon points for a shape of radius r, centred at (cx, cy), turned by rot degrees
function shapePoints(kind, cx, cy, r, rot) {
  const a = (rot * Math.PI) / 180;
  const pt = (x, y) => [cx + x * Math.cos(a) - y * Math.sin(a), cy + x * Math.sin(a) + y * Math.cos(a)];
  if (kind === "square") return [[-r, -r], [r, -r], [r, r], [-r, r]].map(([x, y]) => pt(x * 0.75, y * 0.75));
  if (kind === "triangle") return [-90, 30, 150].map((d) => pt(r * Math.cos((d * Math.PI) / 180), r * Math.sin((d * Math.PI) / 180)));
  if (kind === "cross") {
    const w = r * 0.2;
    const plus = [[-w, -r], [w, -r], [w, -w], [r, -w], [r, w], [w, w], [w, r], [-w, r], [-w, w], [-r, w], [-r, -w], [-w, -w]];
    return plus.map(([x, y]) => pt((x - y) * Math.SQRT1_2, (x + y) * Math.SQRT1_2));
  }
  return null; // circle
}
function shapePath(kind, cx, cy, r, rot) {
  if (r <= 0) return `M${cx} ${cy}Z`;
  if (kind === "circle") return `M${cx - r} ${cy}a${r} ${r} 0 1 0 ${2 * r} 0a${r} ${r} 0 1 0 ${-2 * r} 0Z`;
  return "M" + shapePoints(kind, cx, cy, r, rot).map((p) => p.map((v) => v.toFixed(1)).join(" ")).join("L") + "Z";
}
// small shape as an SVG, for the mark, orbits and pops
function shapeSvg(kind, size, mode = "fill") {
  const sw = Math.max(4, size / 9), c = size / 2, r = size / 2 - 4 - (mode === "fill" ? 0 : sw / 2); // keep the stroke inside the box
  const style = mode === "fill" ? `fill:${SHAPE_COLOR[kind]}` : `fill:none;stroke:${SHAPE_COLOR[kind]};stroke-width:${sw}`;
  return `<svg aria-hidden="true" viewBox="0 0 ${size} ${size}" width="${size}" height="${size}" class="sh-${kind}"><path style="${style}" d="${shapePath(kind, c, c, kind === "square" ? r * 1.3 : r, 0)}"/></svg>`;
}
function markMarkup(px) {
  const s = Math.round(px * 0.46);
  return ["triangle", "circle", "cross", "square"].map((k) => shapeSvg(k, s)).join("");
}
function markIn(tl, sel, at) {
  tl.fromTo(`${sel} > svg`, { scale: 0, rotation: -160, transformOrigin: "50% 50%" }, { scale: 1, rotation: 0, duration: 0.5, ease: "back.out(2.2)", stagger: 0.06 }, at);
}

// the shape cover: grows from the centre spinning until the frame is covered, then a hole of the same shape opens
// el: the .cover element (its children ride inside the clip); ring: an <svg> path drawn at the edge in the shape's colour
function shapeCover(tl, el, ring, kind, W, H, at, inDur, outAt, outDur) {
  const cx = W / 2, cy = H / 2, R = COVER_R[kind];
  const s = { r: 0, rot: -40, hole: 0, hrot: 0 };
  const coverEl = document.querySelector(el), ringEl = document.querySelector(ring);
  ringEl.setAttribute("style", `fill:none;stroke:${SHAPE_COLOR[kind]};stroke-width:28`);
  const paint = () => {
    if (s.hole <= 0) {
      coverEl.style.clipPath = `path("${shapePath(kind, cx, cy, s.r, s.rot)}")`;
      ringEl.setAttribute("d", shapePath(kind, cx, cy, s.r * 1.04 + 10, s.rot));
    } else {
      coverEl.style.clipPath = `path(evenodd, "M0 0H${W}V${H}H0Z${shapePath(kind, cx, cy, s.hole, s.hrot)}")`;
      ringEl.setAttribute("d", shapePath(kind, cx, cy, s.hole * 0.96 - 10, s.hrot));
    }
  };
  paint();
  tl.to(s, { r: R, rot: 0, duration: inDur, ease: "power3.in", onUpdate: paint }, at);
  if (outAt != null) tl.fromTo(s, { hole: 0.001, hrot: 30 }, { hole: R, hrot: 0, duration: outDur, ease: "power3.out", onUpdate: paint, immediateRender: false }, outAt);
}

// the name repeated in walls, solid and outline rows in turn, drifting in opposite directions
function wallMarkup(word, rows, size) {
  const line = (word + " ").repeat(8);
  return Array.from({ length: rows }, (_, i) => `<div class="wall-row ${i % 2 ? "line" : "solid"}" style="font-size:${size}px">${line}</div>`).join("");
}
function wallDrift(tl, sel, at, dur, dist) {
  document.querySelectorAll(`${sel} .wall-row`).forEach((row, i) => {
    const dir = i % 2 ? 1 : -1;
    tl.fromTo(row, { x: dir > 0 ? -dist : 0 }, { x: dir > 0 ? 0 : -dist, duration: dur, ease: "none" }, at);
  });
}

// wrap each letter in a mask so it can rise into place
function splitChars(sel) {
  document.querySelectorAll(sel).forEach((el) => {
    el.innerHTML = [...el.textContent].map((c) => (c === " " ? " " : `<span class="mask"><span class="ch">${c}</span></span>`)).join("");
  });
}
function charsIn(tl, sel, at, each = 0.03) {
  tl.fromTo(`${sel} .ch`, { yPercent: 110, rotation: 8 }, { yPercent: 0, rotation: 0, duration: 0.45, ease: "back.out(1.6)", stagger: each }, at);
}
function charsOut(tl, sel, at) {
  tl.to(`${sel} .ch`, { yPercent: -115, duration: 0.22, ease: "power3.in", stagger: 0.012 }, at);
}
// a tag slams in from the left with a little overshoot
function tagIn(tl, sel, at) {
  tl.fromTo(sel, { xPercent: -120, opacity: 0 }, { xPercent: 0, opacity: 1, duration: 0.4, ease: "back.out(1.8)" }, at);
}
// shrink a one-line text until it fits maxW (long game names)
function fit(sel, maxW) {
  const el = document.querySelector(sel);
  let fs = parseFloat(getComputedStyle(el).fontSize);
  while (el.scrollWidth > maxW && fs > 20) el.style.fontSize = (fs -= 2) + "px";
}
function kind(sel, k) {
  document.querySelectorAll(sel).forEach((el) => el.classList.add(`k-${["gameplay", "news", "tech"].includes(k) ? k : "gameplay"}`));
}

// subscribe click: coral button, cursor clicks, SUBSCRIBED, four shapes pop out of the bell as it rings
function subscribeMarkup() {
  return `<div class="sub-btn"><span class="sub-a">Subscribe</span><span class="sub-b">Subscribed</span></div>
  <div class="sub-bell"><svg aria-hidden="true" viewBox="0 0 24 24" width="50" height="50"><path fill="currentColor" d="M12 22a2.5 2.5 0 0 0 2.45-2h-4.9A2.5 2.5 0 0 0 12 22zm7-6V11a7 7 0 0 0-5.5-6.84V3.5a1.5 1.5 0 0 0-3 0v.66A7 7 0 0 0 5 11v5l-2 2v1h18v-1z"/></svg></div>
  <div class="sub-pops">${["triangle", "circle", "cross", "square"].map((k) => shapeSvg(k, 34)).join("")}</div>
  <svg class="sub-cursor" aria-hidden="true" viewBox="0 0 24 24" width="64" height="64"><path fill="currentColor" d="M4 2l14 11-6 1 4 7-3 1.5-4-7-5 4z"/></svg>`;
}
function subscribeAnim(tl, root, at) {
  const q = (s) => `${root} ${s}`;
  document.querySelectorAll(q(".sub-pops > svg")).forEach((p) => Object.assign(p.style, { position: "absolute", left: "455px", top: "35px", opacity: 0 }));
  tl.fromTo(q(".sub-btn"), { yPercent: 130, rotation: -6, opacity: 0 }, { yPercent: 0, rotation: 0, opacity: 1, duration: 0.45, ease: "back.out(1.8)" }, at);
  tl.fromTo(q(".sub-a"), { scale: 0.4, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.3, ease: "back.out(2)" }, at + 0.22);
  tl.fromTo(q(".sub-cursor"), { x: 260, y: 160, opacity: 0 }, { x: 0, y: 0, opacity: 1, duration: 0.55, ease: "power3.out" }, at + 0.6);
  tl.to(q(".sub-cursor"), { scale: 0.82, duration: 0.08, yoyo: true, repeat: 1 }, at + 1.2);
  tl.to(q(".sub-btn"), { scale: 0.92, duration: 0.08, yoyo: true, repeat: 1 }, at + 1.2);
  tl.set(q(".sub-btn"), { backgroundColor: "var(--color-shade)" }, at + 1.28);
  tl.set(q(".sub-a"), { opacity: 0 }, at + 1.28);
  tl.set(q(".sub-b"), { opacity: 1 }, at + 1.28);
  tl.fromTo(q(".sub-bell"), { scale: 0, rotation: -90 }, { scale: 1, rotation: 0, duration: 0.35, ease: "back.out(2.4)" }, at + 1.45);
  tl.to(q(".sub-cursor"), { x: 250, y: 6, duration: 0.4, ease: "power2.inOut" }, at + 1.55);
  tl.to(q(".sub-cursor"), { scale: 0.82, duration: 0.08, yoyo: true, repeat: 1 }, at + 2.0);
  tl.fromTo(q(".sub-bell svg"), { rotation: 0 }, { keyframes: [{ rotation: 22 }, { rotation: -20 }, { rotation: 12 }, { rotation: 0 }], duration: 0.6, ease: "none", transformOrigin: "50% 10%" }, at + 2.05);
  [[-90, -70], [70, -80], [95, 30], [-80, 45]].forEach(([dx, dy], i) => {
    tl.fromTo(q(`.sub-pops > svg:nth-child(${i + 1})`), { x: 0, y: 0, scale: 0.2, opacity: 1, rotation: 0 }, { x: dx, y: dy, scale: 1, rotation: 180, opacity: 0, duration: 0.7, ease: "power3.out", immediateRender: false }, at + 2.05);
  });
}
