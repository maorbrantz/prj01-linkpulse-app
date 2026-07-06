const API_BASE = window.LINKPULSE_API_BASE || "/api";
const LIVE_INTERVAL_MS = 4000;
const RECENT_LIMIT = 5;

const form = document.getElementById("shorten-form");
const urlInput = document.getElementById("url-input");
const shortenBtn = document.getElementById("shorten-btn");
const result = document.getElementById("result");
const shortLink = document.getElementById("short-link");
const copyButton = document.getElementById("copy-button");
const statsButton = document.getElementById("stats-button");
const stats = document.getElementById("stats");
const statsCode = document.getElementById("stats-code");
const statsTotal = document.getElementById("stats-total");
const chart = document.getElementById("chart");
const liveToggle = document.getElementById("live-toggle");
const recent = document.getElementById("recent");
const recentList = document.getElementById("recent-list");
const errorBox = document.getElementById("error");

let currentCode = null;
let liveTimer = null;
let shownTotal = 0;

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideError();
  shortenBtn.disabled = true;
  shortenBtn.querySelector(".btn-label").textContent = "…";
  try {
    const data = await createLink(urlInput.value);
    currentCode = data.short_code;
    shownTotal = 0;
    shortLink.textContent = data.short_url.replace(/^https?:\/\//, "");
    shortLink.href = data.short_url;
    result.classList.remove("hidden");
    stats.classList.add("hidden");
    stopLive();
    rememberLink(data.short_code, urlInput.value, data.short_url);
    renderRecent();
  } catch (err) {
    showError(err.message);
  } finally {
    shortenBtn.disabled = false;
    shortenBtn.querySelector(".btn-label").textContent = "Shorten";
  }
});

copyButton.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(shortLink.href);
    copyButton.textContent = "copied";
    copyButton.classList.add("copied");
    setTimeout(() => {
      copyButton.textContent = "copy";
      copyButton.classList.remove("copied");
    }, 1600);
  } catch {
    showError("Could not reach the clipboard. Copy the link by hand.");
  }
});

statsButton.addEventListener("click", () => {
  if (currentCode) openStats(currentCode);
});

liveToggle.addEventListener("change", () => {
  liveToggle.checked ? startLive() : stopLive();
});

async function openStats(code) {
  hideError();
  currentCode = code;
  try {
    renderStats(await fetchStats(code));
    stats.classList.remove("hidden");
    stats.scrollIntoView({ behavior: "smooth", block: "nearest" });
  } catch (err) {
    showError(err.message);
  }
}

function startLive() {
  stopLive();
  liveToggle.checked = true;
  liveTimer = setInterval(async () => {
    if (!currentCode) return;
    try {
      renderStats(await fetchStats(currentCode));
    } catch {
      /* transient errors during a refresh should not kill the loop */
    }
  }, LIVE_INTERVAL_MS);
}

function stopLive() {
  liveToggle.checked = false;
  if (liveTimer) clearInterval(liveTimer);
  liveTimer = null;
}

async function createLink(url) {
  const response = await fetch(`${API_BASE}/links`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
  if (!response.ok) {
    throw new Error("Could not shorten that URL. Check the format and try again.");
  }
  return response.json();
}

async function fetchStats(code) {
  const response = await fetch(`${API_BASE}/links/${code}/stats`);
  if (!response.ok) {
    throw new Error("No stats for this link yet. Click it once and try again.");
  }
  return response.json();
}

function renderStats(data) {
  statsCode.textContent = `/${data.short_code}`;
  animateTotal(data.total_clicks);
  drawChart(lastDays(data.daily, 7));
}

function animateTotal(target) {
  const from = shownTotal;
  shownTotal = target;
  if (from === target) {
    statsTotal.textContent = String(target);
    return;
  }
  const start = performance.now();
  const dur = 600;
  const step = (now) => {
    const t = Math.min(1, (now - start) / dur);
    const eased = 1 - Math.pow(1 - t, 3);
    statsTotal.textContent = String(Math.round(from + (target - from) * eased));
    if (t < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

function lastDays(daily, n) {
  const byDay = Object.fromEntries(daily.map((d) => [d.day, d.count]));
  const days = [];
  for (let i = n - 1; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    const key = d.toISOString().slice(0, 10);
    days.push({ day: key, count: byDay[key] || 0 });
  }
  return days;
}

function drawChart(days) {
  const W = 560;
  const H = 180;
  const pad = { top: 26, bottom: 24 };
  const gap = 14;
  const barW = (W - gap * (days.length - 1)) / days.length;
  const max = Math.max(1, ...days.map((d) => d.count));
  const svgNS = "http://www.w3.org/2000/svg";

  chart.replaceChildren();
  const defs = document.createElementNS(svgNS, "defs");
  defs.innerHTML =
    '<linearGradient id="bar-grad" x1="0" y1="0" x2="0" y2="1">' +
    '<stop offset="0" stop-color="#22d3ee"/><stop offset="1" stop-color="#8b5cf6"/>' +
    "</linearGradient>";
  chart.append(defs);

  days.forEach((d, i) => {
    const x = i * (barW + gap);
    const usable = H - pad.top - pad.bottom;
    const h = Math.max(3, Math.round((d.count / max) * usable));
    const y = H - pad.bottom - h;

    const bg = rect(svgNS, x, pad.top, barW, usable, "bar-bg");
    const bar = rect(svgNS, x, y, barW, h, "bar");

    const count = document.createElementNS(svgNS, "text");
    count.setAttribute("x", x + barW / 2);
    count.setAttribute("y", y - 7);
    count.setAttribute("class", "count-label");
    count.textContent = d.count > 0 ? d.count : "";

    const label = document.createElementNS(svgNS, "text");
    label.setAttribute("x", x + barW / 2);
    label.setAttribute("y", H - 6);
    label.setAttribute("class", "day-label");
    label.textContent = d.day.slice(5).replace("-", "/");

    chart.append(bg, bar, count, label);
  });
}

function rect(ns, x, y, w, h, cls) {
  const r = document.createElementNS(ns, "rect");
  r.setAttribute("x", x);
  r.setAttribute("y", y);
  r.setAttribute("width", w);
  r.setAttribute("height", h);
  r.setAttribute("class", cls);
  return r;
}

function rememberLink(code, url, shortUrl) {
  const items = loadRecent().filter((i) => i.code !== code);
  items.unshift({ code, url, shortUrl });
  localStorage.setItem("linkpulse.recent", JSON.stringify(items.slice(0, RECENT_LIMIT)));
}

function loadRecent() {
  try {
    return JSON.parse(localStorage.getItem("linkpulse.recent")) || [];
  } catch {
    return [];
  }
}

function renderRecent() {
  const items = loadRecent();
  if (!items.length) return;
  recentList.replaceChildren();
  for (const item of items) {
    const li = document.createElement("li");
    const code = document.createElement("span");
    code.className = "r-code";
    code.textContent = `/${item.code}`;
    const url = document.createElement("span");
    url.className = "r-url";
    url.textContent = item.url;
    const btn = document.createElement("button");
    btn.className = "ghost";
    btn.type = "button";
    btn.textContent = "pulse";
    btn.addEventListener("click", () => openStats(item.code));
    li.append(code, url, btn);
    recentList.append(li);
  }
  recent.classList.remove("hidden");
}

function showError(message) {
  errorBox.textContent = message;
  errorBox.classList.remove("hidden");
}

function hideError() {
  errorBox.classList.add("hidden");
}

renderRecent();
