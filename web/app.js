"use strict";

const TOKEN = document.querySelector('meta[name="studio-token"]').content;
const INSTANCE = document.querySelector('meta[name="studio-instance"]').content;
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];

// ------------------------------------------------------------------ icons (drawn for this app)
const ICONS = {
  "chevron-down": '<path d="m6 9 6 6 6-6"/>',
  "chevron-up": '<path d="m6 15 6-6 6 6"/>',
  "chevron-left": '<path d="m15 6-6 6 6 6"/>',
  cog: '<circle cx="12" cy="12" r="3.2"/><path d="M12 2.8v2.4M12 18.8v2.4M2.8 12h2.4M18.8 12h2.4M5.5 5.5l1.7 1.7M16.8 16.8l1.7 1.7M5.5 18.5l1.7-1.7M16.8 7.2l1.7-1.7"/><circle cx="12" cy="12" r="6.6"/>',
  clipboard: '<rect x="6" y="4" width="12" height="17" rx="2"/><path d="M9 4.5V3.5h6v1"/><path d="M9.5 11h5M9.5 15h5"/>',
  "clipboard-paste": '<rect x="6" y="4" width="12" height="17" rx="2"/><path d="M9 4.5V3.5h6v1"/><path d="m12 9v7m0 0-3-3m3 3 3-3"/>',
  "file-up": '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/><path d="M12 17v-6m0 0-2.5 2.5M12 11l2.5 2.5"/>',
  folder: '<path d="M3 7.5A2.5 2.5 0 0 1 5.5 5H9l2 2h7.5A2.5 2.5 0 0 1 21 9.5v7a2.5 2.5 0 0 1-2.5 2.5h-13A2.5 2.5 0 0 1 3 16.5z"/>',
  key: '<circle cx="8" cy="15" r="4"/><path d="m11 12 8.5-8.5M16 7l2.5 2.5M14 9l2 2"/>',
  captions: '<rect x="3" y="5" width="18" height="14" rx="3"/><path d="M10 10.5a2 2 0 1 0 0 3M16.5 10.5a2 2 0 1 0 0 3"/>',
  trash: '<path d="M4 7h16M9 7V4.5h6V7M6 7l1 13h10l1-13M10 11v5M14 11v5"/>',
  broom: '<path d="M14 4l6 6M12.5 5.5l6 6-6.5 6.5c-2 2-6 2.5-8.5 2.5 0-2.5.5-6.5 2.5-8.5z"/><path d="M8 15l2 2"/>',
  x: '<path d="M6 6l12 12M18 6 6 18"/>',
  "x-circle": '<circle cx="12" cy="12" r="9"/><path d="m9 9 6 6m0-6-6 6"/>',
  external: '<path d="M14 4h6v6M20 4l-9 9"/><path d="M18 14v4a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4"/>',
  retry: '<path d="M4 12a8 8 0 0 1 13.7-5.6L20 8.7M20 4v4.7h-4.7M20 12a8 8 0 0 1-13.7 5.6L4 15.3M4 20v-4.7h4.7"/>',
  pause: '<rect x="7" y="5" width="3.5" height="14" rx="1"/><rect x="13.5" y="5" width="3.5" height="14" rx="1"/>',
  play: '<path d="M7 5.5v13a1 1 0 0 0 1.5.9l10.4-6.5a1 1 0 0 0 0-1.8L8.5 4.6A1 1 0 0 0 7 5.5z"/>',
  download: '<path d="M12 4v11m0 0-4.5-4.5M12 15l4.5-4.5M4.5 16v2.5A1.5 1.5 0 0 0 6 20h12a1.5 1.5 0 0 0 1.5-1.5V16"/>',
  wrench: '<path d="M14.5 6.5a4 4 0 0 0 5 5L12 19l-2.5.5L9 17zM14.5 6.5 17 4M3.5 7.5l3 3M6.5 4.5l-3 3 4 4 3-3"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5.5M12 7.6v.1"/>',
  check: '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
  warn: '<path d="M12 4 2.8 19.5h18.4zM12 10v4.5M12 17.2v.1"/>',
  film: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m10 9.5 4.5 2.5-4.5 2.5z"/>',
  music: '<path d="M9 18V6l11-2v12"/><circle cx="6.5" cy="18" r="2.5"/><circle cx="17.5" cy="16" r="2.5"/>',
  list: '<path d="M8 6h12M8 12h12M8 18h12M4 6h.01M4 12h.01M4 18h.01"/>',
  copy: '<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V5a1 1 0 0 1 1-1h9"/>',
  refresh: '<path d="M20 12a8 8 0 1 1-2.4-5.7L20 8.7M20 4v4.7h-4.7"/>',
  star: '<path d="m12 3.5 2.6 5.3 5.9.9-4.3 4.1 1 5.8-5.2-2.7-5.2 2.7 1-5.8-4.3-4.1 5.9-.9z"/>',
};
const icon = (n) => `<svg viewBox="0 0 24 24" aria-hidden="true">${ICONS[n] || ""}</svg>`;
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const TRACKS = [["both", "Video + Audio"], ["audio", "Audio"], ["video", "Video"]];
const STAGE_TEXT = {
  "Merging video + audio": "Merging", "Converting audio": "Re-encoding", "Converting video": "Re-encoding",
  "Remuxing": "Remuxing", "Embedding thumbnail": "Finalizing", "Writing metadata": "Finalizing",
  "Embedding subtitles": "Finalizing", "Cutting sponsor segments": "Re-encoding", "Starting": "Initializing",
};
const LANGS = [["en", "English"], ["es", "Spanish"], ["fr", "French"], ["de", "German"], ["it", "Italian"],
  ["pt", "Portuguese"], ["nl", "Dutch"], ["ru", "Russian"], ["uk", "Ukrainian"], ["pl", "Polish"], ["cs", "Czech"],
  ["sv", "Swedish"], ["no", "Norwegian"], ["da", "Danish"], ["fi", "Finnish"], ["el", "Greek"], ["tr", "Turkish"],
  ["ar", "Arabic"], ["he", "Hebrew"], ["hi", "Hindi"], ["ja", "Japanese"], ["ko", "Korean"],
  ["zh-Hans", "Chinese (Simplified)"], ["zh-Hant", "Chinese (Traditional)"], ["id", "Indonesian"], ["th", "Thai"],
  ["vi", "Vietnamese"], ["ro", "Romanian"], ["hu", "Hungarian"]];
const URL_RE = /(?:https?:\/\/|www\.)[^\s<>"'`]+/gi;

let S = { settings: null, tools: {}, login: {}, cookie_browsers: [] };
const jobs = new Map();
const cardEls = new Map();

// ------------------------------------------------------------------ helpers
async function api(path, body = {}) {
  const r = await fetch(path, { method: "POST", headers: { "Content-Type": "application/json", "X-Token": TOKEN }, body: JSON.stringify(body) });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.error || `HTTP ${r.status}`);
  return data;
}
function toast(text, kind = "info", ms = 3800) {
  const el = document.createElement("div");
  el.className = `toast ${kind}`;
  el.innerHTML = icon(kind === "ok" ? "check" : kind === "error" ? "warn" : "info") + `<div>${esc(text)}</div>`;
  $("#toasts").appendChild(el);
  setTimeout(() => { el.classList.add("out"); setTimeout(() => el.remove(), 250); }, ms);
}
const run = (p) => p.catch((e) => toast(e.message, "error"));
function extractUrls(text) {
  const seen = new Set(), out = [];
  for (const m of (text || "").matchAll(URL_RE)) {
    let u = m[0].replace(/[.,;:!?)\]}>'"]+$/, "");
    if (/^www\./i.test(u)) u = "https://" + u;
    if (!seen.has(u)) { seen.add(u); out.push(u); }
  }
  return out;
}
const fmtBytes = (n) => {
  if (!n && n !== 0) return "";
  const u = ["B", "KB", "MB", "GB", "TB"]; let i = 0;
  while (n >= 1024 && i < u.length - 1) { n /= 1024; i++; }
  return `${n.toFixed(n >= 100 || i === 0 ? 0 : 1)} ${u[i]}`;
};
const fmtDur = (s) => {
  if (s == null || isNaN(s)) return "unknown";
  s = Math.round(s);
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), sec = s % 60;
  return (h ? `${h}:${String(m).padStart(2, "0")}` : `${m}`) + `:${String(sec).padStart(2, "0")}`;
};
const fmtDate = (d) => (d && /^\d{8}$/.test(d) ? `${d.slice(0, 4)}-${d.slice(4, 6)}-${d.slice(6)}` : "");
const opt = (v, label, sel) => `<option value="${esc(v)}"${sel ? " selected" : ""}>${esc(label)}</option>`;
const O = () => S.settings.options;

// ------------------------------------------------------------------ live connection
let es = null, offlineTimer = null;
function connect() {
  es = new EventSource(`/api/events?token=${encodeURIComponent(TOKEN)}`);
  es.addEventListener("hello", (e) => { setOffline(false); applyState(JSON.parse(e.data)); });
  es.addEventListener("job", (e) => upsertJob(JSON.parse(e.data)));
  es.addEventListener("removed", (e) => removeCard(JSON.parse(e.data).id));
  es.addEventListener("tools", (e) => { S.tools = JSON.parse(e.data); installing = null; renderBanner(); refreshPage("settings"); });
  es.addEventListener("toast", (e) => { const d = JSON.parse(e.data); toast(d.text, d.kind); });
  es.addEventListener("install", (e) => { installing = JSON.parse(e.data); renderBanner(); });
  es.addEventListener("login", (e) => { S.login = JSON.parse(e.data); onLoginState(); });
  es.onerror = () => {
    clearTimeout(offlineTimer);
    offlineTimer = setTimeout(() => setOffline(true), 1500);
    if (es.readyState === EventSource.CLOSED) waitForServer();
  };
}
async function waitForServer() {
  for (;;) {
    try {
      const d = await (await fetch("/api/ping")).json();
      if (d.instance !== INSTANCE) return location.reload();
      return connect();
    } catch { await new Promise((r) => setTimeout(r, 2000)); }
  }
}
function setOffline(on) { if (!on) clearTimeout(offlineTimer); $("#offline").hidden = !on; }

function applyState(st) {
  S = { ...S, ...st };
  applyTheme();
  for (const id of [...cardEls.keys()]) if (!st.jobs.find((j) => j.id === id)) removeCard(id);
  st.jobs.forEach(upsertJob);
  renderBanner();
  renderHeader();
  renderFooter();
  route();
}
function applyTheme() {
  const t = S.settings.theme || "system";
  if (t === "system") delete document.documentElement.dataset.theme;
  else document.documentElement.dataset.theme = t;
}

// ------------------------------------------------------------------ banner (yt-dlp missing etc.)
let installing = null;
function renderBanner() {
  const t = S.tools || {}, b = $("#banner");
  if (installing) {
    const pct = installing.total ? Math.round((installing.done / installing.total) * 100) : 0;
    b.className = "banner"; b.hidden = false;
    b.innerHTML = `<span class="spinner"></span><span>Downloading yt-dlp… ${pct ? pct + "%" : ""}</span>`;
  } else if (!t.ytdlp) {
    b.className = "banner err"; b.hidden = false;
    b.innerHTML = `${icon("warn")}<span><b>yt-dlp isn't installed.</b> Studio can download the official copy (about 18 MB).</span><span class="grow"></span>
      <button class="btn sm soft" id="bLocate">I already have it…</button><button class="btn sm primary" id="bInstall">Download yt-dlp</button>`;
    $("#bInstall").onclick = installYtdlp;
    $("#bLocate").onclick = locateExe;
  } else if (!t.ffmpeg) {
    b.className = "banner"; b.hidden = false;
    b.innerHTML = `${icon("warn")}<span><b>ffmpeg not found.</b> HD video and audio conversion need it: <code class="mono">winget install Gyan.FFmpeg</code></span>`;
  } else b.hidden = true;
}
async function installYtdlp() { installing = { done: 0, total: 0 }; renderBanner(); run(api("/api/ytdlp/install")); }
async function locateExe() {
  const r = await api("/api/pick-exe", { initial: S.tools.ytdlp || "" });
  if (r.path) { S.tools = r.tools; S.settings.ytdlp_path = r.path; renderBanner(); refreshPage("settings"); toast("Using " + r.path, "ok"); }
}

// ------------------------------------------------------------------ header: add links
const urlInput = $("#urlInput");
function renderHeader() {
  const w = !!S.settings.clipboard_watch;
  urlInput.placeholder = w ? "Watching clipboard: copied links are added to the queue" : "Enter a video/playlist link to add to the queue";
  urlInput.classList.toggle("watching", w);
  $("#mWatch span").textContent = w ? "Stop watching clipboard" : "Watch clipboard";
  $("#mWatch").classList.toggle("active", w);
}
async function addLinks(text, quiet = false) {
  const urls = extractUrls(text);
  if (!urls.length) { if (!quiet) toast("No valid links found in the input/file.", "error"); return 0; }
  const r = await api("/api/add", { text: urls.join("\n") });
  if (r.error) { toast(r.error, "error"); return 0; }
  let msg = r.added === 1 ? "Link added to queue." : `${r.added} links added to queue.`;
  if (r.dupes) msg += ` ${r.dupes} already in the queue.`;
  if (r.added || r.dupes) toast(msg, r.added ? "ok" : "info", 2500);
  if (location.hash && location.hash !== "#/") location.hash = "#/";
  return r.added;
}
$("#addForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  if (await run(addLinks(urlInput.value))) urlInput.value = "";
});
function toggleMenu(menu, btn) {
  const open = menu.hidden;
  $$(".menu").forEach((m) => (m.hidden = true));
  menu.hidden = !open;
}
$("#addMore").addEventListener("click", (e) => { e.stopPropagation(); toggleMenu($("#addMenu")); });
$("#trashMore").addEventListener("click", (e) => { e.stopPropagation(); renderFooter(); toggleMenu($("#trashMenu")); });
document.addEventListener("click", (e) => { if (!e.target.closest(".menu")) $$(".menu").forEach((m) => (m.hidden = true)); });
$("#mWatch").addEventListener("click", async () => {
  const on = !S.settings.clipboard_watch;
  const r = await api("/api/settings", { clipboard_watch: on });
  S.settings = r.settings; renderHeader(); $("#addMenu").hidden = true;
});
$("#mPaste").addEventListener("click", async () => { $("#addMenu").hidden = true; const r = await api("/api/clipboard"); run(addLinks(r.text)); });
$("#mImport").addEventListener("click", () => { $("#addMenu").hidden = true; $("#importFile").click(); });
$("#importFile").addEventListener("change", async (e) => {
  const f = e.target.files[0]; e.target.value = "";
  if (!f) return;
  try { run(addLinks(await f.text())); } catch { toast("Could not read that file.", "error"); }
});
document.addEventListener("paste", (e) => {
  if (e.target.closest("input, textarea, select")) return;
  const text = e.clipboardData.getData("text");
  if (text) { e.preventDefault(); run(addLinks(text)); }
});
let dragDepth = 0;
document.addEventListener("dragenter", (e) => { e.preventDefault(); dragDepth++; $("#dropOverlay").hidden = false; });
document.addEventListener("dragleave", () => { if (--dragDepth <= 0) { dragDepth = 0; $("#dropOverlay").hidden = true; } });
document.addEventListener("dragover", (e) => e.preventDefault());
document.addEventListener("drop", async (e) => {
  e.preventDefault(); dragDepth = 0; $("#dropOverlay").hidden = true;
  const file = e.dataTransfer.files?.[0];
  const text = file ? await file.text() : (e.dataTransfer.getData("text/uri-list") || e.dataTransfer.getData("text/plain"));
  if (text) run(addLinks(text));
});

// ------------------------------------------------------------------ media cards
function qualityList(j, track) {
  const list = (j.qualities && j.qualities[track]) || (S.generic_qualities || {})[track] || [];
  return list;
}
function selectedQuality(list, value) {
  if (list.some((o) => o.value === value)) return value;
  const prefix = list.find((o) => value && value !== "best" && o.value.startsWith(value + "f"));
  return prefix ? prefix.value : "best";
}
function stepOf(j) {
  if (j.status === "ready" && (j.info_state === "loading" || j.info_state === "pending") && S.settings.fetch_info) return "fetch";
  if (j.status === "ready") return "configure";
  if (j.status === "queued" || j.status === "running") return "download";
  return j.status; // paused | done | error | cancelled
}
function progressHTML(cls, pct, label) {
  return `<div class="progress ${cls}"><div class="fill" style="width:${pct}%"></div><span class="label">${esc(label)}</span></div>`;
}
function downloadView(j) {
  const busy = j.status === "queued" || j.stage !== "Downloading";
  let label;
  if (j.status === "queued") label = "Waiting for a free slot…";
  else if (busy) label = `${STAGE_TEXT[j.stage] || j.stage || "Initializing"}…`;
  else {
    const cat = j.kind === "audio" ? "audio" : j.parts > 1 ? (j.part_idx <= 0 ? "video" : "audio") : "video";
    label = `Downloading ${cat}… · ${j.percent.toFixed(2)}%`;
  }
  if (j.item) label += ` · ${j.item[0]} of ${j.item[1]}`;
  const meta = busy ? "" : `<p>ETA: ${j.eta != null ? fmtDur(j.eta) : "unknown"}</p><p>Speed: ${j.speed ? fmtBytes(j.speed) + "/s" : "unknown"}</p>`;
  return { indet: busy, pct: busy ? 0 : j.percent, label, meta };
}
function bodyHTML(j, step) {
  const title = `<h2 class="card-title" title="${esc(j.title || j.url)}">${esc(j.title || j.url)}</h2>`;
  switch (step) {
    case "fetch":
      return `<h2 class="card-title" title="${esc(j.url)}">${esc(j.url)}</h2>${progressHTML("indet", 0, "Fetching metadata…")}<div class="card-row"></div>`;
    case "configure": {
      const list = qualityList(j, j.track);
      const sel = selectedQuality(list, j.quality);
      const chosen = list.find((o) => o.value === sel);
      const qOpts = j.format_override
        ? opt("__exact", `Exact: ${j.format_override}`, true) + list.map((o) => opt(o.value, o.label, false)).join("")
        : list.map((o) => opt(o.value, o.label, o.value === sel)).join("");
      const info = j.is_playlist
        ? `<p>Items: ${j.entries ?? "?"}</p>`
        : `<p>Duration: ${j.duration ? fmtDur(j.duration) : "unknown"}</p>
           <p>Size: ${chosen && chosen.size ? `~${fmtBytes(chosen.size)} <span class="tip" title="The amount of data that will be downloaded.\nNot the final size of the file.">${icon("info")}</span>` : "unknown"}</p>`;
      const warn = j.info_state === "failed" ? `<span class="note" title="${esc(j.info_error || "")}">Couldn't load details: ${esc(j.info_error || "")}</span>` : "";
      return `${title}
        <div class="join"><select class="select primary join-item" data-field="track" aria-label="Select track to download">
          ${TRACKS.map(([v, l]) => opt(v, l, v === j.track)).join("")}</select>
          <select class="select primary join-item" data-field="quality" aria-label="Select format of the track">${qOpts}</select></div>
        <div class="card-row">${info}${warn}</div>`;
    }
    case "download": {
      const d = downloadView(j);
      return `${title}${progressHTML(d.indet ? "indet" : "", d.pct, d.label)}<div class="card-row dl-meta">${d.meta}</div>`;
    }
    case "paused":
      return `${title}${progressHTML("warning", j.percent, `Download paused · ${j.percent.toFixed(2)}%`)}<div class="card-row"><p class="muted">Resume to continue where it stopped.</p></div>`;
    case "done": {
      const extra = j.stage && j.stage !== "Done" ? `<p class="muted">${esc(j.stage)}</p>` : j.files.length > 1 ? `<p class="muted">${j.files.length} files</p>` : "";
      const has = j.files.length > 0;
      return `${title}${progressHTML("", 100, "Download complete · 100%")}
        <div class="card-row">${extra}</div>
        <div class="btns"><button class="btn primary" data-act="reveal"${has ? "" : ` title="Location unknown"`}>Show folder</button>
          <button class="btn primary" data-act="open"${has ? "" : " disabled"}>${j.files.length > 1 ? "Open first file" : "Open file"}</button></div>`;
    }
    case "cancelled":
    case "error": {
      const short = j.status === "cancelled" ? "Download cancelled" : `Error: ${(j.error || "Failed").split(/[.:]/)[0].slice(0, 60)}`;
      return `${title}${progressHTML("error", 100, short)}
        <p class="msg">${esc(j.status === "cancelled" ? "Stopped before it finished. Retry to continue." : j.error || "")}</p>
        <div class="btns"><a class="btn soft" href="#/media/${j.id}/logs">Show full log</a>
          ${/sign in|login|members|private|age|cookies/i.test(j.error || "") ? `<a class="btn soft" href="#/auth">Log in</a>` : ""}</div>`;
    }
  }
  return title;
}
function actionsHTML(j, step) {
  const b = (act, ic, tip, disabled) => `<button class="act" data-act="${act}" data-tip="${tip}" aria-label="${tip}"${disabled ? " disabled" : ""}>${icon(ic)}</button>`;
  let third;
  if (j.status === "error" || j.status === "cancelled") third = b("retry", "retry", "Retry download");
  else if (j.status === "running" || j.status === "queued") third = b("pause", "pause", "Pause download");
  else if (j.status === "paused") third = b("start", "play", "Resume download");
  else third = b("start", "download", "Download individually", j.status === "done" || step === "fetch");
  return b("remove", "x-circle", "Remove") + b("link", "external", "Visit on external link") + third +
    b("prefs", "wrench", "Download preferences", ["running", "queued", "done"].includes(j.status)) +
    b("info", "info", "Show metadata");
}
function upsertJob(j) {
  const prev = jobs.get(j.id);
  jobs.set(j.id, j);
  let el = cardEls.get(j.id);
  if (!el) {
    el = document.createElement("article");
    el.className = "card";
    el.dataset.id = j.id;
    el.innerHTML = `<figure></figure><div class="card-body"></div><div class="hdiv"></div><aside class="actions"></aside>`;
    $("#cards").prepend(el);
    cardEls.set(j.id, el);
  }
  const step = stepOf(j);
  el.classList.toggle("ok", j.status === "done");
  el.classList.toggle("bad", j.status === "error");

  const fig = $("figure", el);
  const figSig = `${j.thumbnail}|${j.duration}|${j.entries}|${j.kind}`;
  if (fig.dataset.sig !== figSig) {
    fig.dataset.sig = figSig;
    fig.innerHTML = (j.thumbnail ? `<img src="${esc(j.thumbnail)}" alt="" referrerpolicy="no-referrer" onerror="this.remove()">` : icon(j.kind === "audio" ? "music" : j.is_playlist ? "list" : "film")) +
      (j.duration ? `<span class="badge">${fmtDur(j.duration)}</span>` : j.is_playlist && j.entries ? `<span class="badge">${j.entries} items</span>` : "");
  }

  const body = $(".card-body", el);
  if (step === "download" && body.dataset.step === "download" && body.dataset.title === (j.title || j.url)) {
    // update in place so the bar animates smoothly
    const d = downloadView(j), p = $(".progress", body);
    p.classList.toggle("indet", d.indet);
    $(".fill", p).style.width = d.pct + "%";
    $(".label", p).textContent = d.label;
    $(".dl-meta", body).innerHTML = d.meta;
  } else {
    const html = bodyHTML(j, step);
    const editing = body.contains(document.activeElement) && document.activeElement.tagName === "SELECT";
    if (body.dataset.html !== html && !editing) {
      body.innerHTML = html;
      body.dataset.html = html;
    }
  }
  body.dataset.step = step;
  body.dataset.title = j.title || j.url;

  const acts = actionsHTML(j, step), ae = $(".actions", el);
  if (ae.dataset.sig !== acts) { ae.innerHTML = acts; ae.dataset.sig = acts; }

  if (prev && prev.status !== "done" && j.status === "done") notify(j);
  if (page.kind === "media" && page.id === j.id) refreshPage("media");
  renderFooterSoon();
}
function removeCard(id) {
  jobs.delete(id);
  cardEls.get(id)?.remove();
  cardEls.delete(id);
  renderFooterSoon();
  if (page.kind === "media" && page.id === id) location.hash = "#/";
}
function notify(j) {
  if (!S.settings.notifications || !("Notification" in window) || Notification.permission !== "granted") return;
  if (document.hasFocus()) return;
  new Notification("Download complete", { body: j.title || j.url });
}

$("#cards").addEventListener("change", (e) => {
  const sel = e.target.closest("select[data-field]");
  if (!sel) return;
  const id = +sel.closest(".card").dataset.id;
  const j = jobs.get(id);
  if (sel.dataset.field === "track") run(api("/api/job-options", { id, options: { track: sel.value, quality: "best" } }));
  else if (sel.value !== "__exact") run(api("/api/job-options", { id, options: { quality: sel.value } }));
  sel.blur();
  void j;
});
$("#cards").addEventListener("click", async (e) => {
  const btn = e.target.closest("[data-act]");
  if (!btn) return;
  const id = +btn.closest(".card").dataset.id, j = jobs.get(id);
  switch (btn.dataset.act) {
    case "remove": return run(api("/api/remove", { id }));
    case "link": return run(api("/api/open-url", { url: j.url }));
    case "start": if (needFolder()) return; askNotify(); return run(api("/api/start", { id }));
    case "retry": if (needFolder()) return; return run(api("/api/start", { id }));
    case "pause": return run(api("/api/pause", { id }));
    case "prefs": location.hash = `#/media/${id}/preferences`; return;
    case "info": location.hash = `#/media/${id}/metadata`; return;
    case "reveal": return run(j.files[0] ? api("/api/reveal", { path: j.files[0] }) : api("/api/open-folder", { path: j.folder }));
    case "open": return run(api("/api/open-file", { path: j.files[0] }));
  }
});

// ------------------------------------------------------------------ footer
let footerTimer = null;
function renderFooterSoon() { if (!footerTimer) footerTimer = setTimeout(() => { footerTimer = null; renderFooter(); }, 80); }
function renderFooter() {
  if (!S.settings) return;
  const all = [...jobs.values()];
  const count = (...st) => all.filter((j) => st.includes(j.status)).length;
  const ready = count("ready", "paused"), active = count("running", "queued"), done = count("done");
  const p = $("#totalProgress");
  let pct = 0, label;
  if (active) {
    const total = active + done + count("error");
    const partial = all.filter((j) => j.status === "running").reduce((a, j) => a + j.percent / 100, 0);
    pct = ((done + count("error") + partial) / total) * 100;
    label = `Downloading queue - ${done} of ${total} completed.`;
  } else if (done && !ready) {
    pct = 100;
    label = `Download complete · ${done} item${done === 1 ? "" : "s"} downloaded.`;
  } else {
    label = `Ready to download! ${ready} item${ready === 1 ? "" : "s"} queued.`;
  }
  $(".fill", p).style.width = pct + "%";
  $(".label", p).textContent = label;
  $("#downloadAll").disabled = ready === 0;
  $("#trashBtn").disabled = all.length === 0;
  $("#empty").hidden = all.length > 0;
  document.title = active ? `${Math.round(pct)}% · yt-dlp Studio` : "yt-dlp Studio";

  const sel = (q) => $(`#trashMenu [data-${q}]`);
  sel('clear="done"').disabled = !count("done");
  sel('clear="error"').disabled = !count("error", "cancelled");
  sel('clear="pending"').disabled = !count("ready", "queued", "paused");
  sel('queue="cancel"').disabled = !active;
  sel('queue="pause"').disabled = !active;
  sel('queue="resume"').disabled = !count("paused");

  const o = O();
  $("#authBtn").classList.toggle("on", !!o.cookies || !!S.settings.secrets?.has_password);
  $("#locBtn").classList.toggle("warn", !(o.folder || "").trim());
  $("#authBtn").title = $("#authBtn").classList.contains("on") ? "Edit log in" : "Log in";
  $("#subsBtn").classList.toggle("on", !!o.subtitles);

  const gT = $("#gTrack");
  if (document.activeElement !== gT) gT.innerHTML = TRACKS.map(([v, l]) => opt(v, l, v === o.track)).join("");
  const gQ = $("#gQuality");
  if (document.activeElement !== gQ) {
    const pending = all.filter((j) => ["ready", "paused"].includes(j.status));
    const seen = new Map();
    for (const j of pending) for (const q of qualityList(j, o.track)) if (!seen.has(q.value)) seen.set(q.value, q.label);
    if (!seen.size) for (const q of (S.generic_qualities || {})[o.track] || []) seen.set(q.value, q.label);
    const items = [...seen].sort((a, b) => rankQ(b[0]) - rankQ(a[0]));
    gQ.innerHTML = opt("", "Select format", !seen.has(o.quality)) + items.map(([v, l]) => opt(v, l, v === o.quality)).join("");
  }
}
function rankQ(v) {
  if (v === "best") return 1e9;
  const m = /^h(\d+)(?:f(\d+))?$/.exec(v) || /^a(\d+)$/.exec(v);
  return m ? +m[1] * 1000 + (+m[2] || 0) : 0;
}
$("#gTrack").addEventListener("change", (e) => { O().track = e.target.value; O().quality = "best"; run(api("/api/apply-all", { track: e.target.value, quality: "best" })); e.target.blur(); renderFooter(); });
$("#gQuality").addEventListener("change", (e) => { if (!e.target.value) return; O().quality = e.target.value; run(api("/api/apply-all", { quality: e.target.value })); e.target.blur(); });
$("#downloadAll").addEventListener("click", () => { if (needFolder()) return; askNotify(); run(api("/api/start", {})); });
$("#trashBtn").addEventListener("click", () => run(api("/api/clear", { which: "all" })));
$("#trashMenu").addEventListener("click", (e) => {
  const b = e.target.closest("button");
  if (!b || b.disabled) return;
  $("#trashMenu").hidden = true;
  if (b.dataset.clear) return run(api("/api/clear", { which: b.dataset.clear }));
  if (b.dataset.queue === "cancel") return run(api("/api/cancel-all", {}));
  if (b.dataset.queue === "pause") return run(api("/api/cancel-all", { pause: true }));
  if (b.dataset.queue === "resume") return run(api("/api/start", {}));
});
function needFolder() {
  if ((O().folder || "").trim()) return false;
  toast("Choose where to save downloads first.", "error");
  location.hash = "#/location";
  setTimeout(() => { const f = $("#dl"); if (f) { f.focus(); f.classList.add("unset"); } }, 50);
  return true;
}
function askNotify() {
  if (S.settings.notifications && "Notification" in window && Notification.permission === "default") Notification.requestPermission();
}

// ------------------------------------------------------------------ full pages (hash routes)
let page = { kind: "home" };
let draft = null;          // working copy of settings for the open page
let draftBase = "";
const changed = () => draft && JSON.stringify(draft) !== draftBase;

window.addEventListener("hashchange", route);
function route() {
  if (!S.settings) return;
  const parts = location.hash.replace(/^#\/?/, "").split("/").filter(Boolean);
  const [kind, a, b] = parts;
  if (!kind) page = { kind: "home" };
  else if (kind === "media") page = { kind, id: +a, tab: b || "metadata" };
  else if (kind === "settings") page = { kind, tab: a || "downloads" };
  else page = { kind };
  const home = page.kind === "home";
  $("#home").hidden = !home;
  $("#page").hidden = home;
  if (!home) {
    draft = { options: structuredClone(O()), settings: pick(S.settings, ["max_concurrent", "js_runtime", "fetch_info", "auto_start", "theme", "notifications", "clipboard_watch"]), secrets: { username: S.settings.secrets?.username || "" } };
    draftBase = JSON.stringify(draft);
    renderPage();
    $("#main").scrollTop = 0;
  }
}
const pick = (o, keys) => Object.fromEntries(keys.map((k) => [k, o[k]]));
function refreshPage(kind) { if (page.kind === kind) renderPage(true); }

function subnav(title, { save = true, right = "" } = {}) {
  return `<nav class="subnav"><a class="btn soft" href="#/">${icon("chevron-left")}Back</a>${title}
    <div class="right">${right}${save ? `<button class="btn primary" id="saveBtn" type="button" disabled>Save</button>` : ""}</div></nav>`;
}
function updateSave() { const b = $("#saveBtn"); if (b) b.disabled = !changed(); }

function renderPage(keepDraft = false) {
  const el = $("#page");
  const R = { location: pageLocation, auth: pageAuth, subtitles: pageSubtitles, settings: pageSettings, media: pageMedia }[page.kind];
  if (!R) { el.innerHTML = subnav(`<h1>Not found</h1>`, { save: false }); return; }
  const scroll = $("#main").scrollTop;
  el.innerHTML = R();
  $$("[data-icon]", el).forEach((x) => x.insertAdjacentHTML("afterbegin", icon(x.dataset.icon)));
  bindDraft(el);
  updateSave();
  $("#saveBtn")?.addEventListener("click", saveDraft);
  if (keepDraft) $("#main").scrollTop = scroll;
  PAGE_INIT[page.kind]?.(el);
}

// Inputs bound to the draft: data-bind="options.folder" (value), data-bind-check="options.x" (checkbox)
function getPath(path) { return path.split(".").reduce((o, k) => (o == null ? o : o[k]), draft); }
function setPath(path, v) { const ks = path.split("."); const last = ks.pop(); ks.reduce((o, k) => o[k], draft)[last] = v; }
function bindDraft(el) {
  $$("[data-bind]", el).forEach((inp) => {
    const v = getPath(inp.dataset.bind);
    if (inp.type === "checkbox") inp.checked = !!v; else inp.value = v ?? "";
    inp.addEventListener(inp.type === "checkbox" || inp.tagName === "SELECT" ? "change" : "input", () => {
      let val = inp.type === "checkbox" ? inp.checked : inp.value;
      if (inp.dataset.num != null) val = +val;
      setPath(inp.dataset.bind, val);
      updateSave();
      inp.dispatchEvent(new CustomEvent("bound", { bubbles: true }));
    });
  });
  $$(".seg[data-bind-seg]", el).forEach((seg) => {
    const path = seg.dataset.bindSeg;
    const paint = () => $$("button", seg).forEach((b) => b.classList.toggle("on", b.dataset.v === String(getPath(path))));
    paint();
    seg.addEventListener("click", (e) => {
      const b = e.target.closest("button"); if (!b) return;
      setPath(path, b.dataset.v); paint(); updateSave();
      seg.dispatchEvent(new CustomEvent("bound", { bubbles: true }));
    });
  });
}
async function saveDraft() {
  const btn = $("#saveBtn");
  btn.disabled = true; btn.innerHTML = `<span class="spinner"></span>`;
  try {
    const base = JSON.parse(draftBase);
    if (JSON.stringify(draft.options) !== JSON.stringify(base.options)) {
      await api("/api/options", { options: draft.options });
      S.settings.options = structuredClone(draft.options);
    }
    if (JSON.stringify(draft.settings) !== JSON.stringify(base.settings)) {
      const r = await api("/api/settings", draft.settings);
      S.settings = r.settings; S.tools = r.tools;
      if (draft.settings.notifications && "Notification" in window && Notification.permission === "default") Notification.requestPermission();
    }
    const sec = {};
    if (draft.secrets.username !== base.secrets.username) sec.username = draft.secrets.username;
    if (draft.secrets.password !== undefined) sec.password = draft.secrets.password;
    if (draft.secrets.video_password !== undefined) sec.video_password = draft.secrets.video_password;
    if (Object.keys(sec).length) S.settings = (await api("/api/secrets", sec)).settings;
    applyTheme(); renderHeader(); renderFooter(); renderBanner();
    draft.secrets = { username: S.settings.secrets?.username || "" };
    draftBase = JSON.stringify(draft);
    toast("Saved", "ok", 1500);
    renderPage(true);
  } catch (e) {
    toast(e.message, "error");
    btn.textContent = "Save"; updateSave();
  }
}
const PAGE_INIT = {};

// ---------- Locations
function pageLocation() {
  return subnav(`<h1>Locations</h1>`) + `<section class="page-body">
    <div class="field"><label for="dl">Download folder</label>
      <div class="row" style="flex-wrap:nowrap"><div class="combo">
        <input id="dl" class="input mono" data-bind="options.folder" spellcheck="false" placeholder="Click Browse to choose where downloads go">
        <button class="combo-btn" id="recentBtn" type="button" aria-label="Recent folders" data-icon="chevron-down"></button>
        <ul class="menu" id="recentMenu" hidden></ul></div>
        <button class="btn soft" id="browseBtn" type="button" data-icon="folder">Browse</button>
        <button class="btn subtle square" id="openDl" type="button" title="Open in Explorer" data-icon="external"></button></div>
      <span class="hint">Downloads are saved here.</span></div>
    <div class="divider"></div>
    <div class="field"><span class="label-strong">If the file name already exists</span>
      <div class="seg" data-bind-seg="options.on_exists"><button data-v="keep_both">Keep both</button><button data-v="skip">Skip</button><button data-v="overwrite">Overwrite</button></div>
      <span class="hint" id="existsHint"></span></div>
    <div class="divider"></div>
    <div class="field"><label for="tpl">File name</label>
      <select id="tpl" class="select" data-bind="options.template">
        ${opt("title", "Title")}${opt("title_id", "Title [video ID]")}${opt("uploader_title", "Channel - Title")}${opt("date_title", "Upload date - Title")}${opt("custom", "Custom template…")}
      </select>
      <input class="input mono" id="tplCustom" data-bind="options.template_custom" placeholder="%(title)s.%(ext)s" spellcheck="false">
      <span class="hint">Custom templates use <a href="https://github.com/yt-dlp/yt-dlp#output-template" id="tplHelp" style="text-decoration:underline">yt-dlp's output template</a> syntax.</span></div>
  </section>`;
}
PAGE_INIT.location = (el) => {
  const hints = { keep_both: "New copies are saved as “Title (2).mp4”. Nothing gets overwritten.", skip: "If the file is already there, it isn't downloaded again.", overwrite: "Existing files with the same name are replaced." };
  const paint = () => { $("#existsHint").textContent = hints[draft.options.on_exists] || ""; $("#tplCustom").hidden = draft.options.template !== "custom"; };
  paint();
  el.addEventListener("bound", paint);
  $("#tplHelp").onclick = (e) => { e.preventDefault(); run(api("/api/open-url", { url: e.target.href })); };
  $("#browseBtn").onclick = async () => {
    const r = await api("/api/pick-folder", { initial: draft.options.folder });
    if (r.path) { draft.options.folder = r.path; $("#dl").value = r.path; S.settings.recent_folders = r.recent_folders; updateSave(); }
  };
  $("#openDl").onclick = () => run(api("/api/open-folder", { path: draft.options.folder }));
  $("#recentBtn").onclick = (e) => {
    e.stopPropagation();
    const m = $("#recentMenu");
    const items = [...new Set([S.default_folder, ...(S.settings.recent_folders || [])])].filter(Boolean);
    m.innerHTML = `<li class="menu-title">Recent folders</li>` + items.map((f) => `<li><button type="button" data-folder="${esc(f)}">${icon("folder")}<span class="menu-path">${esc(f)}</span></button></li>`).join("");
    toggleMenu(m);
  };
  $("#recentMenu").onclick = (e) => {
    const b = e.target.closest("[data-folder]"); if (!b) return;
    draft.options.folder = b.dataset.folder; $("#dl").value = b.dataset.folder; $("#recentMenu").hidden = true; updateSave();
  };
};

// ---------- Authentication
function pageAuth() {
  const L = S.login || {};
  const sources = [["", "Don't use a login"], ["studio", "My Studio sign-ins (recommended)"], ["file", "A cookies.txt file"],
    ...S.cookie_browsers.map((b) => [b, `Cookies from ${b[0].toUpperCase() + b.slice(1)}`])];
  const sec = S.settings.secrets || {};
  return subnav(`<h1>Authentication</h1>`) + `<section class="page-body">
    <div class="fieldset"><div class="legend">Sign in inside Studio <span class="badge-pill">Recommended</span></div>
      <span class="label">Log in to a site in Studio's own private browser window, then close it. Studio keeps the login for downloads that need an account: members-only, private, age-restricted or paid videos.</span>
      ${L.browser ? "" : `<div class="status-line err">${icon("warn")}Signing in needs Microsoft Edge or Google Chrome.</div>`}
      <div class="site-grid" id="siteGrid">${(L.quick_sites || []).map(([n, u]) => `<button class="btn soft" type="button" data-site="${esc(u)}">${esc(n)}</button>`).join("")}
        ${(S.settings.custom_sites || []).map((s) => `<span class="site-custom"><button class="btn soft" type="button" data-site="${esc(s.url)}" title="${esc(s.url)}">${icon("star")}${esc(s.name)}</button><button class="site-x" type="button" data-unsite="${esc(s.url)}" title="Remove this button" aria-label="Remove ${esc(s.name)}">${icon("x")}</button></span>`).join("")}</div>
      <div class="row" style="flex-wrap:nowrap;max-width:640px"><input class="input grow" id="otherSite" placeholder="Any other site, e.g. patreon.com/login" spellcheck="false">
        <button class="btn soft" type="button" id="saveSite" title="Add a button for this site to the list above" data-icon="star">Save to list</button>
        <button class="btn primary" type="button" id="openSite">Open sign-in window</button></div>
      <div id="loginStatus"></div>
      <div id="loginSites"></div>
      <span class="hint">For YouTube, a second Google account is safer: Google can flag accounts used with download tools. Logins are stored only on this PC (data\\cookies.txt); anyone with that file could use your sessions.</span>
    </div>
    <div class="divider"></div>
    <div class="fieldset"><div class="legend">Cookies</div>
      <span class="label">Which login downloads should use.</span>
      <div class="field" style="margin:4px 0 0"><select class="select" data-bind="options.cookies" id="cookieSrc">${sources.map(([v, l]) => opt(v, l)).join("")}</select></div>
      <div class="row" id="cookieFileRow" style="flex-wrap:nowrap;max-width:640px"><input class="input mono grow" data-bind="options.cookies_file" placeholder="Path to cookies.txt" spellcheck="false">
        <button class="btn soft" type="button" id="pickCookies">Browse</button></div>
      <span class="hint" id="cookieHint"></span>
    </div>
    <div class="divider"></div>
    <div class="fieldset"><div class="legend">Advanced methods</div>
      <span class="label">Only some sites accept a username and password directly (YouTube doesn't). Passwords are encrypted with your Windows account.</span>
      <div class="grid-2" style="margin-top:6px">
        <div class="field"><label for="u">Username</label><input class="input" id="u" data-bind="secrets.username" autocomplete="off" spellcheck="false"></div>
        <div class="field"><label for="pw">Password</label><input class="input" id="pw" type="password" autocomplete="new-password" placeholder="${sec.has_password ? "•••••••• (saved, type to replace)" : ""}"></div>
      </div>
      <div class="field"><label for="vpw">Video password</label><input class="input" id="vpw" type="password" autocomplete="new-password" style="max-width:300px" placeholder="${sec.has_video_password ? "•••••••• (saved, type to replace)" : "For password-protected videos (e.g. Vimeo)"}"></div>
      ${sec.has_password || sec.has_video_password ? `<div><button class="btn soft sm" type="button" id="clearPw">Forget saved passwords</button></div>` : ""}
    </div>
  </section>`;
}
function renderLoginBits() {
  const L = S.login || {}, st = $("#loginStatus"), sites = $("#loginSites");
  if (!st) return;
  let html = "";
  if (L.busy) html = `<div class="status-line"><span class="spinner"></span>Saving your logins…</div>`;
  else if (L.waiting) html = `<div class="status-line"><span class="spinner"></span>The sign-in window is open. Log in, then close that window and Studio saves it automatically.
    <span class="grow"></span><button class="btn sm primary" type="button" id="saveNow">I'm done, save now</button></div>`;
  else if (L.error) html = `<div class="status-line err">${icon("warn")}${esc(L.error)}</div>`;
  else if (L.notice && !L.saved_at) html = `<div class="status-line">${icon("info")}${esc(L.notice)}</div>`;
  else if (L.saved_at) html = `<div class="status-line ok">${icon("check")}Logins saved ${new Date(L.saved_at * 1000).toLocaleString()}.</div>`;
  st.innerHTML = html;
  $("#saveNow")?.addEventListener("click", () => run(api("/api/login/save")));
  const list = L.sites || [];
  sites.innerHTML = list.length ? `<div class="label" style="margin-bottom:6px">Saved logins (${list.length} sites)</div>
    <div class="chips">${list.slice(0, 60).map((s) => `<span class="chip chip-x">${esc(s.site)}<button type="button" data-forget="${esc(s.site)}" title="Sign out of ${esc(s.site)}" aria-label="Remove saved login for ${esc(s.site)}">${icon("x")}</button></span>`).join("")}</div>
    <span class="hint">Click × on a site to delete just that login.</span>
    <div style="margin-top:10px"><button class="btn soft sm danger" type="button" id="signOutAll">Sign out of everything</button></div>` : "";
  $("#signOutAll")?.addEventListener("click", () => { if (confirm("Delete all saved logins and the sign-in browser profile?")) run(api("/api/login/clear")); });
  sites.onclick = (e) => {
    const b = e.target.closest("[data-forget]");
    if (!b) return;
    if (confirm(`Delete the saved login for ${b.dataset.forget}?\n\nYou'll be signed out of it in Studio's sign-in window too.`)) run(api("/api/login/forget", { site: b.dataset.forget }));
  };
}
let forgetting = false;
let shownNotice = null;
function onLoginState() {
  if (S.login && S.login.busy && page.kind === "auth") forgetting = forgetting || !!$("#loginSites [data-forget]");
  if (page.kind === "auth") renderLoginBits();
  const L = S.login;
  if (L && L.notice && L.notice !== shownNotice) { shownNotice = L.notice; toast(L.notice, "info", 9000); }
  if (L && !L.busy && !L.error && L.last_count && L.saved_at && O().cookies === "") {
    // First successful sign-in: use it right away.
    run(api("/api/options", { options: { cookies: "studio" } }).then(() => {
      O().cookies = "studio";
      if (draft) { draft.options.cookies = "studio"; draftBase = JSON.stringify({ ...JSON.parse(draftBase), options: { ...JSON.parse(draftBase).options, cookies: "studio" } }); }
      renderFooter(); if (page.kind === "auth") renderPage(true);
      toast("Logins saved. Downloads will now use them.", "ok");
    }));
  } else if (L && !L.busy && !L.error && L.last_count == null && page.kind === "auth" && forgetting) {
    forgetting = false; toast("Login removed.", "ok", 2000);
  } else if (L && L.saved_at && !L.busy && !L.waiting && !L.error && L.last_count != null) {
    toast(`Saved logins for ${L.sites.length} site${L.sites.length === 1 ? "" : "s"}.`, "ok", 2500);
  }
}
PAGE_INIT.auth = () => {
  renderLoginBits();
  const paint = () => {
    const v = draft.options.cookies;
    $("#cookieFileRow").hidden = v !== "file";
    $("#cookieHint").textContent = v === "studio" ? ((S.login.sites || []).length ? "Uses the sites you signed in to above." : "Sign in to a site above first.")
      : ["chrome", "edge", "brave", "opera", "vivaldi"].includes(v) ? "Chrome-based browsers often block this on Windows. Studio sign-ins or Firefox work more reliably." : "";
  };
  paint();
  $("#page").addEventListener("bound", paint);
  const open = (url) => run(api("/api/login/open", { url }).then((st) => { S.login = st; renderLoginBits(); }));
  $("#siteGrid").onclick = async (e) => {
    const x = e.target.closest("[data-unsite]");
    if (x) {
      const r = await api("/api/login/sites", { action: "remove", url: x.dataset.unsite });
      S.settings.custom_sites = r.custom_sites; return renderPage(true);
    }
    const b = e.target.closest("[data-site]"); if (b) open(b.dataset.site);
  };
  $("#saveSite").onclick = async () => {
    const url = $("#otherSite").value.trim();
    if (!url) return toast("Type the site's address (ideally its login page) first", "error");
    let guess = url.replace(/^https?:\/\//, "").replace(/^www\./, "").split("/")[0];
    const name = prompt("Name for this button:", guess);
    if (name === null) return;
    const r = await api("/api/login/sites", { action: "add", url, name });
    if (r.error) return toast(r.error, "error");
    S.settings.custom_sites = r.custom_sites; renderPage(true); toast(`Added “${name || guess}”`, "ok", 1800);
  };
  $("#openSite").onclick = () => { const v = $("#otherSite").value.trim(); if (!v) return toast("Type a website first", "error"); open(v); };
  $("#otherSite").onkeydown = (e) => { if (e.key === "Enter") $("#openSite").click(); };
  $("#pickCookies").onclick = async () => {
    const r = await api("/api/pick-cookies", { initial: draft.options.cookies_file });
    if (r.path) { draft.options.cookies_file = r.path; $("[data-bind='options.cookies_file']").value = r.path; updateSave(); }
  };
  $("#pw").oninput = (e) => { draft.secrets.password = e.target.value || undefined; if (!e.target.value) delete draft.secrets.password; updateSave(); };
  $("#vpw").oninput = (e) => { draft.secrets.video_password = e.target.value || undefined; if (!e.target.value) delete draft.secrets.video_password; updateSave(); };
  $("#clearPw")?.addEventListener("click", async () => { S.settings = (await api("/api/secrets", { password: "", video_password: "" })).settings; toast("Saved passwords removed", "ok"); renderPage(true); renderFooter(); });
};

// ---------- Subtitles
function pageSubtitles() {
  return subnav(`<h1>Subtitles</h1>`) + `<section class="page-body">
    <label class="switch-row"><input type="checkbox" class="toggle" data-bind="options.subtitles"><span class="txt"><span>Download subtitles</span><span class="hint">Saved next to the video, or embedded into it.</span></span></label>
    <div id="subOpts">
      <div class="divider"></div>
      <div class="fieldset"><div class="legend">Languages</div>
        <label class="switch-row"><input type="checkbox" class="toggle" data-bind="options.sub_all"><span>Download all languages</span></label>
        <div class="field" style="max-width:420px;margin:4px 0"><input class="input" type="search" id="langSearch" placeholder="Search languages"></div>
        <ul class="lang-list scroll" id="langList"></ul>
      </div>
      <div class="divider"></div>
      <div class="fieldset"><div class="legend">Options</div>
        <label class="switch-row"><input type="checkbox" class="toggle" data-bind="options.sub_auto"><span class="txt"><span>Include auto-generated subtitles</span><span class="hint">Used when there are no proper subtitles.</span></span></label>
        <label class="switch-row"><input type="checkbox" class="toggle" data-bind="options.sub_embed"><span>Embed subtitles into the video</span></label>
        <div class="field" style="margin-top:8px"><label for="sf">Format</label><select id="sf" class="select" style="max-width:200px" data-bind="options.sub_format">${opt("srt", "SRT")}${opt("vtt", "VTT")}${opt("ass", "ASS")}${opt("original", "Original")}</select></div>
      </div>
    </div>
  </section>`;
}
PAGE_INIT.subtitles = (el) => {
  const paintList = () => {
    const q = ($("#langSearch").value || "").toLowerCase();
    const sel = new Set(draft.options.sub_langs || []);
    $("#langList").innerHTML = LANGS.filter(([c, n]) => !q || n.toLowerCase().includes(q) || c.toLowerCase().includes(q))
      .map(([c, n]) => `<li><label><input type="checkbox" class="checkbox" data-lang="${c}"${sel.has(c) ? " checked" : ""}${draft.options.sub_all ? " disabled" : ""}><span>${n}</span><span class="code">${c}</span></label></li>`).join("");
  };
  const paint = () => { $("#subOpts").style.opacity = draft.options.subtitles ? 1 : .45; paintList(); };
  paint();
  el.addEventListener("bound", paint);
  $("#langSearch").oninput = paintList;
  $("#langList").onchange = (e) => {
    const c = e.target.dataset.lang; if (!c) return;
    const set = new Set(draft.options.sub_langs || []);
    e.target.checked ? set.add(c) : set.delete(c);
    draft.options.sub_langs = LANGS.map(([x]) => x).filter((x) => set.has(x));
    updateSave();
  };
};

// ---------- Settings
function pageSettings() {
  const tabs = [["downloads", "Downloads"], ["app", "App"], ["network", "Network"], ["system", "System"], ["about", "About"]];
  const tabBar = `<div class="tabs" role="tablist">${tabs.map(([t, l]) => `<a role="tab" class="tab${page.tab === t ? " active" : ""}" href="#/settings/${t}">${l}</a>`).join("")}</div>`;
  const body = { downloads: settingsDownloads, app: settingsApp, network: settingsNetwork, system: settingsSystem, about: settingsAbout }[page.tab] || settingsDownloads;
  return subnav(tabBar, { save: page.tab !== "about" }) + `<section class="page-body">${body()}</section>`;
}
const sw = (bind, label, hint = "") => `<label class="switch-row"><input type="checkbox" class="toggle" data-bind="${bind}"><span class="txt"><span>${label}</span>${hint ? `<span class="hint">${hint}</span>` : ""}</span></label>`;
function settingsDownloads() {
  return `<div class="grid-2">
      <div class="field"><label>Downloads at once</label><select class="select" data-bind="settings.max_concurrent" data-num>${[1, 2, 3, 4, 5].map((n) => opt(n, n)).join("")}</select></div>
      <div class="field"><label>Video format</label><select class="select" data-bind="options.video_container">${opt("mp4", "MP4 (plays everywhere)")}${opt("mkv", "MKV")}${opt("webm", "WebM")}${opt("original", "Original")}</select></div>
      <div class="field"><label>Audio format</label><select class="select" data-bind="options.audio_format">${opt("mp3", "MP3")}${opt("m4a", "M4A (AAC)")}${opt("opus", "Opus")}${opt("flac", "FLAC (lossless)")}${opt("wav", "WAV")}${opt("original", "Original")}</select></div>
    </div>
    <div class="divider"></div>
    <div class="fieldset"><div class="legend">Playlists</div>
      <div class="field"><span class="label">When a link is part of a playlist, download</span>
        <div class="seg" data-bind-seg="options.playlist"><button data-v="single">Just the video</button><button data-v="all">The whole playlist</button></div></div>
      <div class="row" id="plExtra"><input class="input mono" style="width:220px" data-bind="options.playlist_items" placeholder="Items, e.g. 1-10 (optional)">
        <label class="switch-row" style="padding:0"><input type="checkbox" class="toggle" data-bind="options.playlist_folder"><span>Put each playlist in its own folder</span></label></div>
    </div>
    <div class="divider"></div>
    <div class="fieldset"><div class="legend">Processing</div>
      ${sw("options.embed_thumbnail", "Embed thumbnail")}
      ${sw("options.embed_metadata", "Embed title, artist and other info")}
      ${sw("options.embed_chapters", "Embed chapters")}
      ${sw("options.sponsorblock", "Cut sponsor segments", "Uses SponsorBlock to remove sponsors, self-promotion and reminders to subscribe.")}
      ${sw("options.archive", "Never download the same video twice", "Remembers everything you've downloaded and skips repeats.")}
      ${sw("options.restrict_names", "Plain ASCII file names", "No spaces, emoji or special characters.")}
    </div>
    <div class="divider"></div>
    <div class="fieldset"><div class="legend">Queue</div>
      ${sw("settings.auto_start", "Start downloading as soon as a link is added")}
      ${sw("settings.fetch_info", "Look up title, thumbnail and formats when a link is added")}
    </div>`;
}
PAGE_INIT.settings = (el) => {
  if (page.tab === "downloads") {
    const paint = () => { $("#plExtra").hidden = draft.options.playlist !== "all"; };
    paint(); el.addEventListener("bound", paint);
  }
  if (page.tab === "system") {
    $("#sysUpdate").onclick = () => run(api("/api/ytdlp/update"));
    $("#sysInstall").onclick = installYtdlp;
    $("#sysLocate").onclick = locateExe;
    $("#sysAuto").onclick = async () => { const r = await api("/api/settings", { ytdlp_path: "" }); S.settings = r.settings; S.tools = r.tools; renderPage(true); renderBanner(); };
  }
};
function settingsApp() {
  return `<div class="field"><span class="label-strong">Theme</span>
      <div class="seg" data-bind-seg="settings.theme"><button data-v="system">System</button><button data-v="dark">Dark</button><button data-v="light">Light</button></div></div>
    <div class="divider"></div>
    ${sw("settings.notifications", "Notify me when a download finishes", "Shows a Windows notification when Studio isn't in front.")}
    ${sw("settings.clipboard_watch", "Watch clipboard", "Links you copy anywhere are added to the queue automatically.")}`;
}
function settingsNetwork() {
  return `<div class="field"><label>Speed limit</label><input class="input mono" style="max-width:300px" data-bind="options.rate_limit" placeholder="No limit (e.g. 5M = 5 MB/s)"></div>
    <div class="field"><label>Proxy</label><input class="input mono" data-bind="options.proxy" placeholder="e.g. socks5://user:pass@host:1080" spellcheck="false">
      <span class="hint">Send only Studio's downloads through a proxy. Many VPN services offer a SOCKS5 address.</span></div>
    <div class="divider"></div>
    <div class="field"><label>Extra yt-dlp arguments</label><input class="input mono" data-bind="options.extra" placeholder="e.g. --write-description" spellcheck="false">
      <span class="hint">Added to every download. For advanced users.</span></div>`;
}
function settingsSystem() {
  const t = S.tools || {};
  return `<div class="fieldset"><div class="legend">yt-dlp ${t.version ? `<span class="badge-pill">${esc(t.version)}</span>` : `<span class="badge-pill warn">not installed</span>`}</div>
      <span class="label mono">${esc(t.ytdlp || "Not found")}</span>
      <div class="row"><button class="btn soft sm" type="button" id="sysUpdate" data-icon="refresh">Update</button><button class="btn soft sm" type="button" id="sysInstall" data-icon="download">Download fresh copy</button>
        <button class="btn soft sm" type="button" id="sysLocate">Locate…</button><button class="btn soft sm" type="button" id="sysAuto">Auto-detect</button></div></div>
    <div class="divider"></div>
    <div class="fieldset"><div class="legend">ffmpeg ${t.ffmpeg ? `<span class="badge-pill">found</span>` : `<span class="badge-pill warn">missing</span>`}</div>
      <span class="label mono">${esc(t.ffmpeg || "Install with: winget install Gyan.FFmpeg")}</span></div>
    <div class="divider"></div>
    <div class="field"><label>JavaScript runtime</label><select class="select" style="max-width:300px" data-bind="settings.js_runtime">${opt("auto", `Auto-detect${t.js ? ` (${t.js})` : ""}`)}${opt("deno", "Deno")}${opt("node", "Node.js")}${opt("bun", "Bun")}${opt("none", "None")}</select>
      <span class="hint">YouTube needs one to unlock every quality.</span></div>`;
}
function settingsAbout() {
  return `<div class="fieldset"><div class="legend">yt-dlp Studio</div>
    <span class="label">A friendly front end for yt-dlp. This is an AI-generated app, written with Claude. Not affiliated with yt-dlp or Open Video Downloader, whose interface it's modelled on.</span>
    <dl class="kv" style="margin-top:12px"><dt>yt-dlp</dt><dd>${esc(S.tools.version || "not installed")}</dd><dt>ffmpeg</dt><dd>${S.tools.ffmpeg ? "found" : "missing"}</dd><dt>JS runtime</dt><dd>${esc(S.tools.js || "none")}</dd></dl></div>`;
}

// ---------- Media (metadata / logs / preferences)
let mediaData = null;
function pageMedia() {
  const j = jobs.get(page.id);
  if (!j) return subnav(`<h1>Item not found</h1>`, { save: false });
  const tabs = [["metadata", "Metadata"], ["logs", "Logs"], ["preferences", "Preferences"]];
  const tabBar = `<div class="tabs">${tabs.map(([t, l]) => `<a class="tab${page.tab === t ? " active" : ""}" href="#/media/${j.id}/${t}">${l}</a>`).join("")}</div>`;
  const action = j.status === "paused" ? `<button class="btn primary" style="background:var(--warning);color:#000" type="button" id="mediaGo">Resume</button>`
    : ["ready", "error", "cancelled"].includes(j.status) ? `<button class="btn primary" type="button" id="mediaGo">Download</button>` : "";
  return subnav(tabBar, { save: page.tab === "preferences" && ["ready", "paused", "error", "cancelled"].includes(j.status), right: action }) +
    `<section class="page-body" id="mediaBody"><span class="spinner"></span></section>`;
}
PAGE_INIT.media = async () => {
  const id = page.id;
  $("#mediaGo")?.addEventListener("click", () => { if (!needFolder()) run(api("/api/start", { id })); });
  const r = await api("/api/job", { id }).catch(() => null);
  if (!r || r.error || page.kind !== "media" || page.id !== id) return;
  mediaData = r;
  const body = $("#mediaBody");
  if (page.tab === "logs") {
    body.innerHTML = `<div class="field" style="max-width:none"><label>Command</label><div class="cmd-box">${esc(r.command)}</div></div>
      <div class="row" style="justify-content:space-between;margin-bottom:8px"><span class="label">yt-dlp output</span><button class="btn soft sm" type="button" id="copyLog" data-icon="copy">Copy</button></div>
      <pre class="log scroll" id="logPre">${r.log.map((l) => (l.startsWith("ERROR") ? `<span class="e">${esc(l)}</span>` : l.startsWith("WARNING") ? `<span class="w">${esc(l)}</span>` : esc(l))).join("\n") || '<span class="muted">No output yet.</span>'}</pre>`;
    $$("[data-icon]", body).forEach((x) => x.insertAdjacentHTML("afterbegin", icon(x.dataset.icon)));
    const pre = $("#logPre"); pre.scrollTop = pre.scrollHeight;
    $("#copyLog").onclick = async () => { await navigator.clipboard.writeText(r.command + "\n\n" + pre.textContent); toast("Log copied", "ok", 1500); };
  } else if (page.tab === "preferences") {
    renderPrefs(body, r);
  } else {
    const j = r.job, m = r.meta || {};
    const rows = [["Title", j.title], ["Channel", m.channel || m.uploader || j.uploader], ["Duration", j.duration && fmtDur(j.duration)],
      ["Uploaded", fmtDate(m.upload_date)], ["Views", m.view_count?.toLocaleString()], ["Likes", m.like_count?.toLocaleString()],
      ["Items", j.is_playlist ? j.entries : null], ["Site", m.extractor_key], ["Link", j.url], ["Download", j.label],
      ["Saved to", j.files[0] || null], ["Formats", r.formats.length || null]].filter(([, v]) => v != null && v !== "");
    body.innerHTML = `<div class="meta-grid">${j.thumbnail ? `<img src="${esc(j.thumbnail)}" alt="" referrerpolicy="no-referrer">` : `<div></div>`}
      <dl class="kv">${rows.map(([k, v]) => `<dt>${k}</dt><dd>${esc(v)}</dd>`).join("")}</dl></div>
      ${m.description ? `<div class="divider"></div><div class="label" style="margin-bottom:6px">Description</div><div class="desc scroll">${esc(m.description)}</div>` : ""}
      ${j.info_state === "failed" ? `<div class="divider"></div><div class="status-line err">${icon("warn")}${esc(j.info_error || "Couldn't load details")}</div>` : ""}`;
  }
};
function renderPrefs(body, r) {
  const j = r.job;
  const editable = ["ready", "paused", "error", "cancelled"].includes(j.status);
  const fs = r.formats || [];
  const video = fs.filter((f) => f.vcodec && f.vcodec !== "none").sort((a, b) => (b.height || 0) - (a.height || 0) || (b.tbr || 0) - (a.tbr || 0));
  const audio = fs.filter((f) => (!f.vcodec || f.vcodec === "none") && f.acodec && f.acodec !== "none").sort((a, b) => (b.tbr || 0) - (a.tbr || 0));
  const cur = (j.format_override || "").split("+");
  const vSel = video.find((f) => cur.includes(f.id))?.id || "", aSel = audio.find((f) => cur.includes(f.id))?.id || "";
  const vLabel = (f) => `${f.height ? f.height + "p" : f.res}${f.fps && f.fps > 30 ? Math.round(f.fps) : ""} · ${f.ext} · ${(f.vcodec || "").split(".")[0]}${f.acodec && f.acodec !== "none" ? " + audio" : ""}${f.size ? " · " + fmtBytes(f.size) : ""} (${f.id})`;
  const aLabel = (f) => `${f.abr || f.tbr ? Math.round(f.abr || f.tbr) + "kbps" : "?"} · ${f.ext} · ${(f.acodec || "").split(".")[0]}${f.size ? " · " + fmtBytes(f.size) : ""}${f.note ? " · " + f.note : ""} (${f.id})`;
  const list = qualityList(j, j.track);
  body.innerHTML = `${editable ? "" : `<div class="status-line" style="margin-bottom:14px">${icon("info")}Preferences can only be changed before the download starts.</div>`}
    <div class="fieldset"><div class="legend">Quality</div>
      <div class="join" style="max-width:480px"><select class="select primary join-item grow" id="pTrack"${editable ? "" : " disabled"}>${TRACKS.map(([v, l]) => opt(v, l, v === j.track)).join("")}</select>
        <select class="select primary join-item grow" id="pQuality"${editable ? "" : " disabled"}>${list.map((o) => opt(o.value, o.label, o.value === selectedQuality(list, j.quality))).join("")}</select></div></div>
    <div class="divider"></div>
    <div class="fieldset"><div class="legend">Exact streams <span class="badge-pill warn">Advanced</span></div>
      <span class="label">Pick the exact video and audio stream to download. Overrides the quality above.</span>
      ${fs.length ? `<div class="join" style="max-width:860px;margin-top:6px">
        <select class="select join-item grow" id="pAudio"${editable ? "" : " disabled"}>${opt("", "Audio track: none")}${audio.map((f) => opt(f.id, aLabel(f), f.id === aSel)).join("")}</select>
        <select class="select join-item grow" id="pVideo"${editable ? "" : " disabled"}>${opt("", "Video track: none")}${video.map((f) => opt(f.id, vLabel(f), f.id === vSel)).join("")}</select></div>
        <span class="hint mono" id="pChoice"></span>` : `<span class="hint">No format list available for this item${j.is_playlist ? " (playlists use the quality above)" : ""}.</span>`}
    </div>
    ${fs.length ? `<div class="divider"></div><details><summary class="label" style="cursor:pointer">All formats (${fs.length})</summary>
      <table class="fmt-table" style="margin-top:8px"><tr><th>ID</th><th>Ext</th><th>Resolution</th><th>FPS</th><th>Video</th><th>Audio</th><th>Size</th><th>Note</th></tr>
      ${fs.map((f) => `<tr><td>${esc(f.id)}</td><td>${esc(f.ext)}</td><td>${esc(f.res)}</td><td>${f.fps ? Math.round(f.fps) : ""}</td><td>${esc((f.vcodec || "").split(".")[0])}</td><td>${esc((f.acodec || "").split(".")[0])}</td><td>${f.size ? fmtBytes(f.size) : ""}</td><td>${esc(f.note)}</td></tr>`).join("")}</table></details>` : ""}`;
  // Preferences use their own draft (job options) rather than settings
  draft.job = { track: j.track, quality: selectedQuality(list, j.quality), format_override: j.format_override || "" };
  draftBase = JSON.stringify(draft);
  const choice = () => { const c = [$("#pVideo")?.value, $("#pAudio")?.value].filter(Boolean).join("+"); if ($("#pChoice")) $("#pChoice").textContent = c ? `-f ${c}` : ""; return c; };
  choice();
  $("#pTrack").onchange = (e) => { draft.job.track = e.target.value; draft.job.quality = "best"; draft.job.format_override = "";
    $("#pQuality").innerHTML = qualityList(j, e.target.value).map((o) => opt(o.value, o.label, o.value === "best")).join(""); updateSave(); };
  $("#pQuality").onchange = (e) => { draft.job.quality = e.target.value; updateSave(); };
  const exact = () => { draft.job.format_override = choice(); updateSave(); };
  $("#pAudio")?.addEventListener("change", exact);
  $("#pVideo")?.addEventListener("change", exact);
  $("#saveBtn")?.replaceWith($("#saveBtn").cloneNode(true));
  $("#saveBtn")?.addEventListener("click", async () => {
    await run(api("/api/job-options", { id: j.id, options: draft.job }));
    draftBase = JSON.stringify(draft); updateSave(); toast("Preferences saved", "ok", 1500);
  });
  updateSave();
}

// ------------------------------------------------------------------ boot
$$("[data-icon]").forEach((el) => el.insertAdjacentHTML("afterbegin", icon(el.dataset.icon)));
window.addEventListener("beforeunload", () => es && es.close());
connect();
