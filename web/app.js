"use strict";

const TOKEN = document.querySelector('meta[name="studio-token"]').content;
const INSTANCE = document.querySelector('meta[name="studio-instance"]').content;
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];

const ICONS = {
  film: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M7 4v16M17 4v16M3 9h4M3 15h4M17 9h4M17 15h4"/>',
  spark: '<path d="M12 3l2.2 5.8L20 11l-5.8 2.2L12 19l-2.2-5.8L4 11l5.8-2.2z"/>',
  music: '<path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>',
  wave: '<path d="M2 12h2M6 8v8M10 5v14M14 8v8M18 10v4M22 12h-2"/>',
  captions: '<rect x="2" y="5" width="20" height="14" rx="2"/><path d="M7 11h3M7 15h7M14 11h3M17 15h0"/>',
  image: '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="9" cy="9" r="2"/><path d="M21 15l-5-5L5 21"/>',
  terminal: '<path d="M4 17l6-5-6-5M12 19h8"/>',
  star: '<path d="M12 3l2.8 5.7 6.2.9-4.5 4.4 1.1 6.2L12 17.3 6.4 20.2l1.1-6.2L3 9.6l6.2-.9z"/>',
  clipboard: '<rect x="8" y="2" width="8" height="4" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>',
  x: '<path d="M18 6L6 18M6 6l12 12"/>',
  folder: '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
  external: '<path d="M15 3h6v6M10 14L21 3M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
  chevron: '<path d="M6 9l6 6 6-6"/>',
  copy: '<rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  download: '<path d="M12 4v11m0 0l-4.5-4.5M12 15l4.5-4.5M5 20h14"/>',
  play: '<path d="M7 4l13 8-13 8z"/>',
  stop: '<rect x="6" y="6" width="12" height="12" rx="2"/>',
  check: '<path d="M20 6L9 17l-5-5"/>',
  refresh: '<path d="M21 12a9 9 0 1 1-2.6-6.4M21 4v5h-5"/>',
  gear: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>',
  info: '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h0"/>',
  sliders: '<path d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6"/>',
  inbox: '<path d="M22 12h-6l-2 3h-4l-2-3H2"/><path d="M5.5 5.1L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.5-6.9A2 2 0 0 0 16.8 4H7.2a2 2 0 0 0-1.7 1.1z"/>',
  warn: '<path d="M10.3 3.9L1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0zM12 9v4M12 17h0"/>',
};
const icon = (name) => `<svg viewBox="0 0 24 24" aria-hidden="true">${ICONS[name] || ""}</svg>`;
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const TOGGLES = [
  { key: "embed_thumbnail", label: "Embed thumbnail", kinds: ["video", "audio"] },
  { key: "embed_metadata", label: "Embed title/artist info", kinds: ["video", "audio"] },
  { key: "embed_chapters", label: "Chapters", kinds: ["video"] },
  { key: "embed_subs", label: "Embed English subtitles", kinds: ["video"] },
  { key: "sponsorblock", label: "Cut sponsor segments", kinds: ["video", "audio"] },
  { key: "archive", label: "Never re-download the same video", kinds: null },
  { key: "restrict_names", label: "Plain ASCII file names", kinds: null },
];
const EXISTS_HINT = {
  keep_both: "New copies are saved as “Title (2).mp4”. Nothing gets overwritten.",
  skip: "If the file is already there, it isn’t downloaded again.",
  overwrite: "Existing files with the same name are replaced.",
};
const URL_RE = /(?:https?:\/\/|www\.)[^\s<>"'`]+/gi;

let S = { settings: null, presets: [], tools: {}, cookie_browsers: [] };
let opts = {};
let activeUserPreset = null;
const jobs = new Map();
const jobEls = new Map();

// ------------------------------------------------------------------ api

async function api(path, body = {}) {
  const r = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Token": TOKEN },
    body: JSON.stringify(body),
  });
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

const debounce = (fn, ms) => { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; };

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
  if (n == null || isNaN(n)) return "";
  const u = ["B", "KB", "MB", "GB", "TB"]; let i = 0;
  while (n >= 1024 && i < u.length - 1) { n /= 1024; i++; }
  return `${n.toFixed(n >= 100 || i === 0 ? 0 : 1)} ${u[i]}`;
};
const fmtDur = (s) => {
  if (s == null || isNaN(s)) return "";
  s = Math.round(s);
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), sec = s % 60;
  return (h ? `${h}:${String(m).padStart(2, "0")}` : `${m}`) + `:${String(sec).padStart(2, "0")}`;
};
const hostOf = (u) => { try { return new URL(u).hostname.replace(/^www\./, ""); } catch { return u; } };

// ------------------------------------------------------------------ live connection

let es = null, offlineTimer = null;

function connect() {
  es = new EventSource(`/api/events?token=${encodeURIComponent(TOKEN)}`);
  es.addEventListener("hello", (e) => { setOffline(false); applyState(JSON.parse(e.data)); });
  es.addEventListener("job", (e) => upsertJob(JSON.parse(e.data)));
  es.addEventListener("removed", (e) => removeJobEl(JSON.parse(e.data).id));
  es.addEventListener("tools", (e) => { S.tools = JSON.parse(e.data); installing = null; renderTools(); });
  es.addEventListener("toast", (e) => { const d = JSON.parse(e.data); toast(d.text, d.kind); });
  es.addEventListener("install", (e) => { installing = JSON.parse(e.data); renderTools(); });
  es.addEventListener("clip", (e) => {
    const added = appendLinks(JSON.parse(e.data).urls.join("\n"));
    if (added) toast(`Picked up ${added} link${added > 1 ? "s" : ""} from the clipboard`, "ok", 2200);
  });
  es.onerror = () => {
    clearTimeout(offlineTimer);
    offlineTimer = setTimeout(() => setOffline(true), 1500);
    if (es.readyState === EventSource.CLOSED) waitForServer();
  };
}

async function waitForServer() {
  for (;;) {
    try {
      const r = await fetch("/api/ping");
      const d = await r.json();
      if (d.instance !== INSTANCE) return location.reload();   // server restarted: new token
      return connect();
    } catch { await new Promise((r) => setTimeout(r, 2000)); }
  }
}

function setOffline(on) {
  if (!on) clearTimeout(offlineTimer);
  $("#offline").hidden = !on;
}

function applyState(st) {
  S = { ...S, ...st };
  opts = { ...st.settings.options };
  $("#watchClip").checked = !!st.settings.clipboard_watch;
  renderPresets();
  renderForm();
  renderTools();
  for (const id of [...jobEls.keys()]) if (!st.jobs.find((j) => j.id === id)) removeJobEl(id);
  st.jobs.forEach(upsertJob);
  updatePreview();
}

// ------------------------------------------------------------------ tool status & banner

let installing = null;

function renderTools() {
  const t = S.tools || {};
  const chips = [];
  chips.push(t.ytdlp
    ? `<span class="chip" title="${esc(t.ytdlp)}"><span class="dot"></span>yt-dlp <b>${esc(t.version || "?")}</b> <button id="chipUpdate">Update</button></span>`
    : `<span class="chip bad"><span class="dot"></span>yt-dlp missing</span>`);
  chips.push(t.ffmpeg
    ? `<span class="chip" title="${esc(t.ffmpeg)}"><span class="dot"></span>ffmpeg</span>`
    : `<span class="chip bad"><span class="dot"></span>ffmpeg missing</span>`);
  chips.push(t.js
    ? `<span class="chip" title="JavaScript runtime used for YouTube"><span class="dot"></span>JS: ${esc(t.js)}</span>`
    : `<span class="chip warn" title="Install Deno or Node.js for full YouTube support"><span class="dot"></span>No JS runtime</span>`);
  $("#tools").innerHTML = chips.join("");
  $("#chipUpdate")?.addEventListener("click", updateYtdlp);

  const b = $("#banner");
  if (installing) {
    const pct = installing.total ? (installing.done / installing.total) * 100 : 5;
    b.className = "banner";
    b.innerHTML = `${icon("download")}<span>Downloading yt-dlp… ${fmtBytes(installing.done)}${installing.total ? " of " + fmtBytes(installing.total) : ""}</span>
      <div class="progress-inline"><div style="width:${pct}%"></div></div>`;
    b.hidden = false;
  } else if (!t.ytdlp) {
    b.className = "banner err";
    b.innerHTML = `${icon("warn")}<span><b>yt-dlp isn't installed.</b> Studio can download the official copy from GitHub (about 18 MB) into its own folder.</span>
      <span class="grow"></span>
      <button class="btn sm" id="bLocate">I already have it…</button>
      <button class="btn primary sm" id="bInstall">${icon("download")}Download yt-dlp</button>`;
    b.hidden = false;
    $("#bInstall").onclick = installYtdlp;
    $("#bLocate").onclick = locateExe;
  } else if (!t.ffmpeg) {
    b.className = "banner";
    b.innerHTML = `${icon("warn")}<span><b>ffmpeg not found.</b> Merging HD video with audio and converting to MP3 need it. Install it with <code class="mono">winget install Gyan.FFmpeg</code>, then restart Studio.</span>`;
    b.hidden = false;
  } else {
    b.hidden = true;
  }
  $("#downloadBtn").disabled = $("#addBtn").disabled = !t.ytdlp;
}

async function installYtdlp() {
  installing = { done: 0, total: 0 }; renderTools();
  try { await api("/api/ytdlp/install"); } catch (e) { installing = null; renderTools(); toast(e.message, "error"); }
}
async function updateYtdlp() { try { await api("/api/ytdlp/update"); } catch (e) { toast(e.message, "error"); } }
async function locateExe() {
  const r = await api("/api/pick-exe", { initial: S.tools.ytdlp || "" });
  if (r.path) { S.tools = r.tools; S.settings.ytdlp_path = r.path; renderTools(); fillSettings(); toast("Using " + r.path, "ok"); }
}

// ------------------------------------------------------------------ presets

function renderPresets() {
  const groups = [
    ["Video", S.presets.filter((p) => p.kind === "video")],
    ["Audio", S.presets.filter((p) => p.kind === "audio")],
    ["Other", S.presets.filter((p) => p.kind === "extra" || p.kind === "custom")],
  ];
  const user = S.settings.user_presets || [];
  let html = groups.map(([name, list]) => `
    <div class="preset-group"><span>${name}</span><div class="preset-row">
      ${list.map((p) => `<button class="preset${!activeUserPreset && opts.preset === p.id ? " on" : ""}" data-preset="${p.id}">
        <span class="ico">${icon(p.icon)}</span><span><div class="t">${esc(p.label)}</div><div class="s">${esc(p.sub)}</div></span></button>`).join("")}
    </div></div>`).join("");
  if (user.length) {
    html += `<div class="preset-group"><span>Mine</span><div class="preset-row">
      ${user.map((p) => {
        const base = S.presets.find((b) => b.id === p.options.preset);
        return `<button class="preset${activeUserPreset === p.id ? " on" : ""}" data-user="${p.id}" title="${esc(p.options.folder || "")}">
          <span class="ico">${icon("star")}</span><span><div class="t">${esc(p.label)}</div><div class="s">${esc(base ? base.label : "")}</div></span>
          <span class="del" data-del="${p.id}" title="Delete preset">${icon("x")}</span></button>`;
      }).join("")}
    </div></div>`;
  }
  $("#presets").innerHTML = html;
}

$("#presets").addEventListener("click", async (e) => {
  const del = e.target.closest("[data-del]");
  if (del) {
    e.stopPropagation();
    const r = await api("/api/presets/delete", { id: del.dataset.del });
    S.settings.user_presets = r.user_presets;
    if (activeUserPreset === del.dataset.del) activeUserPreset = null;
    return renderPresets();
  }
  const b = e.target.closest(".preset");
  if (!b) return;
  if (b.dataset.preset) {
    opts.preset = b.dataset.preset;
    activeUserPreset = null;
  } else {
    const p = S.settings.user_presets.find((x) => x.id === b.dataset.user);
    opts = { ...opts, ...p.options };
    activeUserPreset = p.id;
    renderForm();
  }
  renderPresets();
  renderToggles();
  optsChanged(false);
});

// ------------------------------------------------------------------ options form

function setSeg(el, v) { $$("button", el).forEach((b) => b.classList.toggle("on", b.dataset.v === v)); }

function renderForm() {
  $("#folder").value = opts.folder || "";
  $("#folder").classList.toggle("unset", !opts.folder);
  $("#template").value = opts.template || "title";
  $("#templateCustom").value = opts.template_custom || "";
  $("#templateCustom").hidden = opts.template !== "custom";
  setSeg($("#onExists"), opts.on_exists || "keep_both");
  $("#onExistsHint").textContent = EXISTS_HINT[opts.on_exists || "keep_both"];
  setSeg($("#playlistMode"), opts.playlist || "single");
  $("#playlistExtra").hidden = opts.playlist !== "all";
  $("#playlistItems").value = opts.playlist_items || "";
  $("#playlistFolder").checked = !!opts.playlist_folder;
  $("#cookies").innerHTML = `<option value="">Nothing (default)</option>` +
    S.cookie_browsers.map((b) => `<option value="${b}">${b[0].toUpperCase() + b.slice(1)}</option>`).join("");
  $("#cookies").value = opts.cookies || "";
  $("#rateLimit").value = opts.rate_limit || "";
  $("#extra").value = opts.extra || "";
  renderToggles();
}

function renderToggles() {
  const kind = (S.presets.find((p) => p.id === opts.preset) || {}).kind;
  $("#toggles").innerHTML = TOGGLES.map((t) => {
    const na = t.kinds && !t.kinds.includes(kind);
    return `<span class="toggle${opts[t.key] ? " on" : ""}${na ? " na" : ""}" data-key="${t.key}" role="switch" tabindex="0"
      aria-checked="${!!opts[t.key]}" title="${na ? "Doesn't apply to this choice" : ""}">${icon("check")}${t.label}</span>`;
  }).join("");
}

$("#toggles").addEventListener("click", (e) => {
  const t = e.target.closest(".toggle");
  if (!t) return;
  opts[t.dataset.key] = !opts[t.dataset.key];
  renderToggles();
  optsChanged();
});
$("#toggles").addEventListener("keydown", (e) => {
  if ((e.key === " " || e.key === "Enter") && e.target.classList.contains("toggle")) { e.preventDefault(); e.target.click(); }
});

function bindSeg(id, key, after) {
  $(id).addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    opts[key] = b.dataset.v;
    setSeg($(id), b.dataset.v);
    after?.();
    optsChanged();
  });
}
bindSeg("#onExists", "on_exists", () => { $("#onExistsHint").textContent = EXISTS_HINT[opts.on_exists]; });
bindSeg("#playlistMode", "playlist", () => { $("#playlistExtra").hidden = opts.playlist !== "all"; });

const bindInput = (id, key, prop = "value", evt = "input") =>
  $(id).addEventListener(evt, () => { opts[key] = $(id)[prop]; optsChanged(); });
bindInput("#folder", "folder");
$("#folder").addEventListener("input", () => $("#folder").classList.toggle("unset", !opts.folder));
bindInput("#templateCustom", "template_custom");
bindInput("#playlistItems", "playlist_items");
bindInput("#playlistFolder", "playlist_folder", "checked", "change");
bindInput("#cookies", "cookies", "value", "change");
bindInput("#rateLimit", "rate_limit");
bindInput("#extra", "extra");
$("#template").addEventListener("change", () => {
  opts.template = $("#template").value;
  $("#templateCustom").hidden = opts.template !== "custom";
  if (opts.template === "custom") $("#templateCustom").focus();
  optsChanged();
});

const saveOptions = debounce(() => api("/api/options", { options: opts }).catch(() => {}), 600);
const updatePreview = debounce(async () => {
  try {
    const r = await api("/api/preview", { options: opts, text: $("#links").value });
    $("#cmdPreview").textContent = r.command;
  } catch (e) { $("#cmdPreview").textContent = "⚠ " + e.message; }
}, 120);

function optsChanged(clearUser = true) {
  if (clearUser && activeUserPreset) { activeUserPreset = null; renderPresets(); }
  saveOptions();
  updatePreview();
}

// folder picking
$("#browseBtn").addEventListener("click", async () => {
  $("#browseBtn").disabled = true;
  try {
    const r = await api("/api/pick-folder", { initial: opts.folder });
    if (r.path) {
      opts.folder = r.path; $("#folder").value = r.path;
      $("#folder").classList.remove("unset", "needs");
      S.settings.recent_folders = r.recent_folders;
      optsChanged();
    }
  } catch (e) { toast(e.message, "error"); }
  $("#browseBtn").disabled = false;
});
$("#openFolderBtn").addEventListener("click", async () => {
  if (!(opts.folder || "").trim()) return needFolder();
  api("/api/open-folder", { path: opts.folder }).catch((e) => toast(e.message, "error"));
});

function renderRecent() {
  const list = S.settings.recent_folders || [];
  const def = S.default_folder;
  const items = [...new Set([def, ...list])].filter(Boolean);
  if (!items.length) {
    $("#recentMenu").innerHTML = `<div class="menu-title">No recent folders yet. Use Browse… to pick one.</div>`;
    return;
  }
  $("#recentMenu").innerHTML = `<div class="menu-title">Recent folders</div>` + items.map((f) => `
    <button class="menu-item" data-folder="${esc(f)}" title="${esc(f)}">${icon("folder")}<span>${esc(f)}</span>
      ${f === def ? '<em class="tag">default</em>' : `<i class="x" data-forget="${esc(f)}" title="Remove from list">${icon("x")}</i>`}</button>`).join("");
}
$("#recentBtn").addEventListener("click", (e) => {
  e.stopPropagation();
  const m = $("#recentMenu");
  if (m.hidden) renderRecent();
  m.hidden = !m.hidden;
});
$("#recentMenu").addEventListener("click", async (e) => {
  e.stopPropagation();
  const forget = e.target.closest("[data-forget]");
  if (forget) {
    const r = await api("/api/forget-folder", { path: forget.dataset.forget });
    S.settings.recent_folders = r.recent_folders;
    return renderRecent();
  }
  const it = e.target.closest("[data-folder]");
  if (!it) return;
  opts.folder = it.dataset.folder; $("#folder").value = opts.folder;
  $("#folder").classList.remove("unset", "needs");
  $("#recentMenu").hidden = true;
  optsChanged();
});
document.addEventListener("click", () => { $("#recentMenu").hidden = true; });

// ------------------------------------------------------------------ links box

const links = $("#links");

function updateLinkCount() {
  const n = extractUrls(links.value).length;
  $("#linkCount").innerHTML = n ? `<span class="pill">${n}</span> link${n > 1 ? "s" : ""} ready` : "";
  updatePreview();
}

/** Append any new links from text; returns how many were new. */
function appendLinks(text) {
  const have = new Set(extractUrls(links.value));
  const fresh = extractUrls(text).filter((u) => !have.has(u));
  if (!fresh.length) return 0;
  const cur = links.value.replace(/\s+$/, "");
  links.value = (cur ? cur + "\n" : "") + fresh.join("\n") + "\n";
  links.scrollTop = links.scrollHeight;
  $("#dropzone").classList.remove("flash"); void $("#dropzone").offsetWidth; $("#dropzone").classList.add("flash");
  updateLinkCount();
  return fresh.length;
}

links.addEventListener("input", updateLinkCount);
$("#pasteBtn").addEventListener("click", async () => {
  const r = await api("/api/clipboard");
  if (!appendLinks(r.text)) toast(extractUrls(r.text).length ? "Those links are already in the list" : "No links on the clipboard");
});
$("#clearBtn").addEventListener("click", () => { links.value = ""; updateLinkCount(); links.focus(); });
$("#watchClip").addEventListener("change", async (e) => {
  await api("/api/settings", { clipboard_watch: e.target.checked });
  S.settings.clipboard_watch = e.target.checked;
  if (e.target.checked) toast("Watching the clipboard: copy any link and it lands here", "ok");
});

// paste anywhere (outside inputs) goes to the links box
document.addEventListener("paste", (e) => {
  if (e.target.closest("input, textarea, select, dialog")) return;
  const text = e.clipboardData.getData("text");
  if (text) { e.preventDefault(); appendLinks(text) || toast("No new links in what you pasted"); }
});

// drag links in from a browser
let dragDepth = 0;
document.addEventListener("dragenter", (e) => { e.preventDefault(); dragDepth++; $("#dropzone").classList.add("drag"); });
document.addEventListener("dragleave", () => { if (--dragDepth <= 0) { dragDepth = 0; $("#dropzone").classList.remove("drag"); } });
document.addEventListener("dragover", (e) => e.preventDefault());
document.addEventListener("drop", (e) => {
  e.preventDefault(); dragDepth = 0; $("#dropzone").classList.remove("drag");
  const text = e.dataTransfer.getData("text/uri-list") || e.dataTransfer.getData("text/plain");
  if (text) appendLinks(text) || toast("No new links in what you dropped");
});

// ------------------------------------------------------------------ add / download

function needFolder() {
  toast("Choose where to save downloads first: click Browse…", "error");
  const f = $("#folder");
  f.scrollIntoView({ block: "center", behavior: "smooth" });
  f.classList.remove("needs"); void f.offsetWidth; f.classList.add("needs");
}

async function submit(start) {
  const text = links.value;
  const n = extractUrls(text).length;
  if (!n) { toast("Paste at least one link first", "error"); links.focus(); return; }
  if (!(opts.folder || "").trim()) { needFolder(); return; }
  try {
    const r = await api("/api/add", { text, options: opts, start });
    if (r.need_folder) return needFolder();
    if (r.error) return toast(r.error, "error");
    if (r.recent_folders) S.settings.recent_folders = r.recent_folders;
    links.value = ""; updateLinkCount();
    let msg = start ? `Downloading ${r.added} item${r.added === 1 ? "" : "s"}` : `Added ${r.added} to the queue`;
    if (r.dupes) msg += ` · ${r.dupes} already in the queue`;
    toast(msg, r.added ? "ok" : "info");
  } catch (e) { toast(e.message, "error"); }
}
$("#downloadBtn").addEventListener("click", () => submit(true));
$("#addBtn").addEventListener("click", () => submit(false));
document.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && (e.ctrlKey || e.metaKey) && !e.target.closest("dialog")) { e.preventDefault(); submit(true); }
});

$("#copyCmd").addEventListener("click", async () => {
  try { await navigator.clipboard.writeText($("#cmdPreview").textContent); toast("Command copied", "ok", 1600); }
  catch { toast("Couldn't copy", "error"); }
});

// save as preset
$("#savePresetBtn").addEventListener("click", () => { $("#presetName").value = ""; $("#presetDlg").showModal(); });
$("#presetDlg").addEventListener("close", async () => {
  if ($("#presetDlg").returnValue !== "ok") return;
  const r = await api("/api/presets/save", { name: $("#presetName").value, options: opts });
  S.settings.user_presets = r.user_presets;
  activeUserPreset = r.user_presets[r.user_presets.length - 1].id;
  renderPresets();
  toast("Preset saved", "ok");
});

// ------------------------------------------------------------------ queue

function statusText(j) {
  const item = j.item ? `Item ${j.item[0]} of ${j.item[1]} · ` : "";
  switch (j.status) {
    case "ready": return "Ready, press start";
    case "queued": return "Waiting for a free slot";
    case "running": return item + (j.stage || "Starting");
    case "done": return j.stage || "Done";
    case "cancelled": return "Cancelled";
    case "error": return j.error || "Failed";
  }
  return j.status;
}

function actionsFor(j) {
  const b = (act, ic, title, cls = "") => `<button class="icon-btn ${cls}" data-act="${act}" title="${title}" aria-label="${title}">${icon(ic)}</button>`;
  const out = [];
  if (j.status === "ready") out.push(b("start", "play", "Start"));
  if (j.status === "error" || j.status === "cancelled") out.push(b("start", "refresh", "Retry"));
  if (j.status === "done" && j.files.length) out.push(b("open", "play", "Open file"), b("reveal", "folder", "Show in folder"));
  if (j.status === "done" && !j.files.length) out.push(b("folder", "folder", "Open folder"));
  if (["ready", "error", "cancelled"].includes(j.status) && j.has_formats) out.push(b("formats", "sliders", "Pick formats"));
  out.push(b("log", "info", "Details & log"));
  if (j.status === "running" || j.status === "queued") out.push(b("cancel", "stop", j.status === "queued" ? "Don't start" : "Stop", "danger"));
  else out.push(b("remove", "x", "Remove from list", "danger"));
  return out.join("");
}

function upsertJob(j) {
  jobs.set(j.id, j);
  let el = jobEls.get(j.id);
  if (!el) {
    el = document.createElement("div");
    el.className = "job";
    el.dataset.id = j.id;
    el.innerHTML = `<div class="thumb"></div>
      <div class="job-body"><div class="job-title"></div><div class="job-meta"></div>
        <div class="bar"><div></div></div><div class="job-stats"></div></div>
      <div class="job-actions"></div>`;
    $("#jobs").prepend(el);
    jobEls.set(j.id, el);
  }
  el.dataset.status = j.status;

  const th = $(".thumb", el);
  const bg = j.thumbnail ? `url("${j.thumbnail.replace(/"/g, "%22")}")` : "";
  if (th.style.backgroundImage !== bg) th.style.backgroundImage = bg;
  th.classList.toggle("loading", j.info_state === "loading");
  th.innerHTML = (j.thumbnail ? "" : icon(j.preset_kind === "audio" ? "music" : "film")) +
    (j.duration ? `<span class="dur">${fmtDur(j.duration)}</span>` : j.is_playlist && j.entries ? `<span class="dur">${j.entries} items</span>` : "");

  const t = $(".job-title", el);
  t.textContent = j.title || j.url;
  t.title = j.title ? `${j.title}\n${j.url}` : j.url;
  t.classList.toggle("url", !j.title);

  $(".job-meta", el).innerHTML = `<span class="badge ${esc(j.preset_kind)}">${esc(j.preset_label)}</span>` +
    (j.format_override ? `<span class="badge fmt" title="Custom format">${esc(j.format_override)}</span>` : "") +
    (j.is_playlist ? `<span class="badge">Playlist</span>` : "") +
    `<span class="host">${esc(j.uploader || hostOf(j.url))}</span>`;

  const bar = $(".bar", el);
  const busyStage = j.status === "running" && (j.stage !== "Downloading" || !j.percent);
  bar.classList.toggle("indet", busyStage && j.percent < 100 || (j.status === "running" && j.stage !== "Downloading" && j.stage !== "Starting" && j.percent >= 99.9));
  $("div", bar).style.width = (j.status === "ready" || j.status === "queued" ? 0 : j.percent) + "%";

  const stats = [`<span class="status">${esc(statusText(j))}</span>`];
  if (j.status === "running" && j.stage === "Downloading") {
    stats.push(`<span class="num">${j.percent.toFixed(1)}%</span>`);
    if (j.speed) stats.push(`<span class="num">${fmtBytes(j.speed)}/s</span>`);
    if (j.eta != null) stats.push(`<span class="num">${fmtDur(j.eta)} left</span>`);
  }
  if (j.total && j.status !== "error") stats.push(`<span class="num">${fmtBytes(j.total)}</span>`);
  if (j.status === "done" && j.files.length === 1) {
    stats.push(`<span class="fname" title="${esc(j.files[0])}">${esc(j.files[0].split(/[\\/]/).pop())}</span>`);
  }
  if (j.status === "done" && j.files.length > 1) stats.push(`<span>${j.files.length} files</span>`);
  $(".job-stats", el).innerHTML = stats.join("");

  const acts = actionsFor(j);
  const ae = $(".job-actions", el);
  if (ae.dataset.sig !== acts) { ae.innerHTML = acts; ae.dataset.sig = acts; }

  if (logOpenFor === j.id) refreshLog();
  updateQueueChrome();
}

function removeJobEl(id) {
  jobs.delete(id);
  jobEls.get(id)?.remove();
  jobEls.delete(id);
  updateQueueChrome();
}

function updateQueueChrome() {
  const all = [...jobs.values()];
  const active = all.filter((j) => j.status === "running" || j.status === "queued").length;
  $("#queueCount").textContent = all.length ? `${all.length}${active ? ` · ${active} active` : ""}` : "";
  $("#emptyQueue").hidden = all.length > 0;
  $("#jobs").hidden = all.length === 0;
  $("#startAllBtn").hidden = !all.some((j) => j.status === "ready");
  $("#clearDoneBtn").hidden = !all.some((j) => ["done", "error", "cancelled"].includes(j.status));
  const running = all.filter((j) => j.status === "running");
  document.title = running.length
    ? `${Math.round(running.reduce((a, j) => a + j.percent, 0) / running.length)}% · yt-dlp Studio`
    : "yt-dlp Studio";
}

$("#jobs").addEventListener("click", async (e) => {
  const btn = e.target.closest("[data-act]");
  if (!btn) return;
  const id = +btn.closest(".job").dataset.id;
  const j = jobs.get(id);
  try {
    switch (btn.dataset.act) {
      case "start": await api("/api/start", { id }); break;
      case "cancel": await api("/api/cancel", { id }); break;
      case "remove": await api("/api/remove", { id }); break;
      case "open": await api("/api/open-file", { path: j.files[0] }); break;
      case "reveal": await api("/api/reveal", { path: j.files[0] }); break;
      case "folder": await api("/api/open-folder", { path: j.folder }); break;
      case "formats": openFormats(id); break;
      case "log": openLog(id); break;
    }
  } catch (err) { toast(err.message, "error"); }
});
$("#jobs").addEventListener("dblclick", (e) => {
  const el = e.target.closest(".job");
  if (!el || e.target.closest("button")) return;
  const j = jobs.get(+el.dataset.id);
  if (j.status === "done" && j.files[0]) api("/api/open-file", { path: j.files[0] });
});
$("#startAllBtn").addEventListener("click", () => api("/api/start", {}));
$("#clearDoneBtn").addEventListener("click", () => api("/api/clear-finished"));

// ------------------------------------------------------------------ formats dialog

let fmtJob = null, fmtV = null, fmtA = null;

async function openFormats(id) {
  const r = await api("/api/job", { id });
  fmtJob = id;
  const cur = (r.job.format_override || "").split("+");
  const fs = r.formats;
  const video = fs.filter((f) => f.vcodec && f.vcodec !== "none")
    .sort((a, b) => (b.height || 0) - (a.height || 0) || (b.tbr || 0) - (a.tbr || 0));
  const audio = fs.filter((f) => (!f.vcodec || f.vcodec === "none") && f.acodec && f.acodec !== "none")
    .sort((a, b) => (b.tbr || 0) - (a.tbr || 0));
  fmtV = video.find((f) => cur.includes(f.id))?.id || null;
  fmtA = audio.find((f) => cur.includes(f.id))?.id || null;
  const codec = (c) => (c || "").split(".")[0];
  const row = (f, kind) => `<tr class="pick" data-kind="${kind}" data-id="${esc(f.id)}">
      <td class="id">${esc(f.id)}</td>
      <td>${esc(kind === "v" ? (f.height ? f.height + "p" : f.res) : f.tbr ? Math.round(f.tbr) + "k" : "")}${f.fps && f.fps > 30 ? " " + Math.round(f.fps) : ""}${f.hdr ? '<span class="tag">HDR</span>' : ""}${kind === "v" && f.acodec && f.acodec !== "none" ? '<span class="tag">+audio</span>' : ""}</td>
      <td>${esc(f.ext)}</td>
      <td>${esc(codec(kind === "v" ? f.vcodec : f.acodec))}</td>
      <td>${f.size ? fmtBytes(f.size) : ""}</td>
      <td class="muted">${esc(f.note)}</td></tr>`;
  const head = (k) => `<tr><th>ID</th><th>${k === "v" ? "Quality" : "Bitrate"}</th><th>Ext</th><th>Codec</th><th>Size</th><th>Note</th></tr>`;
  $("#fmtVideo").innerHTML = `<table>${head("v")}${video.map((f) => row(f, "v")).join("")}</table>`;
  $("#fmtAudio").innerHTML = `<table>${head("a")}${audio.map((f) => row(f, "a")).join("")}</table>`;
  $("#formatsTitle").textContent = r.job.title || r.job.url;
  paintFormats();
  $("#formatsDlg").showModal();
}

function fmtChoice() { return [fmtV, fmtA].filter(Boolean).join("+"); }
function paintFormats() {
  $$("#formatsDlg tr.pick").forEach((tr) => tr.classList.toggle("on", tr.dataset.id === (tr.dataset.kind === "v" ? fmtV : fmtA)));
  const c = fmtChoice();
  $("#fmtChoice").textContent = c ? `-f ${c}` : "Click a row to choose. Pick one video and one audio to combine them.";
  $("#fmtOk").disabled = !c;
}
$("#formatsDlg").addEventListener("click", (e) => {
  const tr = e.target.closest("tr.pick");
  if (!tr) return;
  if (tr.dataset.kind === "v") fmtV = fmtV === tr.dataset.id ? null : tr.dataset.id;
  else fmtA = fmtA === tr.dataset.id ? null : tr.dataset.id;
  paintFormats();
});
$("#formatsDlg").addEventListener("close", async () => {
  const v = $("#formatsDlg").returnValue;
  if (v === "ok") await api("/api/format", { id: fmtJob, format: fmtChoice() });
  if (v === "reset") await api("/api/format", { id: fmtJob, format: "" });
});

// ------------------------------------------------------------------ log dialog

let logOpenFor = null;
const refreshLog = debounce(async () => {
  if (logOpenFor == null) return;
  const r = await api("/api/job", { id: logOpenFor }).catch(() => null);
  if (!r || r.error) return;
  $("#logTitle").textContent = r.job.title || r.job.url;
  $("#logCmd").textContent = r.command;
  const pre = $("#logBody");
  const atBottom = pre.scrollTop + pre.clientHeight >= pre.scrollHeight - 20;
  pre.innerHTML = r.log.map((l) => {
    const cls = l.startsWith("ERROR") ? "e" : l.startsWith("WARNING") ? "w" : "";
    return cls ? `<span class="${cls}">${esc(l)}</span>` : esc(l);
  }).join("\n") || '<span class="muted">No output yet.</span>';
  if (atBottom) pre.scrollTop = pre.scrollHeight;
}, 300);
function openLog(id) { logOpenFor = id; $("#logBody").textContent = ""; refreshLog(); $("#logDlg").showModal(); }
$("#logDlg").addEventListener("close", () => { logOpenFor = null; });
$("#logCopy").addEventListener("click", async () => {
  await navigator.clipboard.writeText($("#logCmd").textContent + "\n\n" + $("#logBody").textContent);
  toast("Log copied", "ok", 1600);
});

// ------------------------------------------------------------------ settings dialog

function fillSettings() {
  const s = S.settings;
  $("#setExe").value = S.tools.ytdlp || "Not found";
  $("#setConcurrent").value = String(s.max_concurrent);
  $("#setJs").value = s.js_runtime;
  $("#setFetch").checked = !!s.fetch_info;
}
$("#settingsBtn").addEventListener("click", () => { fillSettings(); $("#settingsDlg").showModal(); });
async function saveSetting(patch) {
  const r = await api("/api/settings", patch);
  S.settings = r.settings; S.tools = r.tools;
  renderTools(); fillSettings();
}
$("#setConcurrent").addEventListener("change", (e) => saveSetting({ max_concurrent: +e.target.value }));
$("#setJs").addEventListener("change", (e) => { saveSetting({ js_runtime: e.target.value }); updatePreview(); });
$("#setFetch").addEventListener("change", (e) => saveSetting({ fetch_info: e.target.checked }));
$("#setExeBrowse").addEventListener("click", locateExe);
$("#setExeAuto").addEventListener("click", () => saveSetting({ ytdlp_path: "" }));
$("#setUpdate").addEventListener("click", updateYtdlp);
$("#setInstall").addEventListener("click", () => { $("#settingsDlg").close(); installYtdlp(); });

// ------------------------------------------------------------------ boot

$$("[data-icon]").forEach((el) => el.insertAdjacentHTML("afterbegin", icon(el.dataset.icon)));
$("#settingsBtn").innerHTML = icon("gear");
$("#recentBtn").innerHTML = icon("chevron");
$("#copyCmd").innerHTML = icon("copy");
$(".empty-icon").innerHTML = icon("inbox");
connect();
links.focus();
