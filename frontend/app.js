/* Shared API helper — same origin, /api/v1 prefix */
const API = "/api/v1";
async function api(path, opts = {}) {
  const res = await fetch(API + path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || JSON.stringify(data) || `HTTP ${res.status}`);
  return data;
}
function msg(el, text, ok = true) {
  const m = typeof el === "string" ? document.querySelector(el) : el;
  m.className = "msg " + (ok ? "ok" : "err");
  m.textContent = text;
  clearTimeout(m._t);
  m._t = setTimeout(() => (m.className = "msg"), 5000);
}
function esc(s) { return String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c])); }
function nav(active) {
  document.querySelectorAll("nav a").forEach(a => {
    if (a.dataset.p === active) a.classList.add("active");
  });
}
