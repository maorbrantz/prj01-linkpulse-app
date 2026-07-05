const API_BASE = window.LINKPULSE_API_BASE || "/api";

const form = document.getElementById("shorten-form");
const urlInput = document.getElementById("url-input");
const result = document.getElementById("result");
const shortLink = document.getElementById("short-link");
const statsButton = document.getElementById("stats-button");
const stats = document.getElementById("stats");
const statsCode = document.getElementById("stats-code");
const statsTotal = document.getElementById("stats-total");
const statsRows = document.getElementById("stats-rows");
const errorBox = document.getElementById("error");

let currentCode = null;

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideError();
  try {
    const data = await createLink(urlInput.value);
    currentCode = data.short_code;
    shortLink.textContent = data.short_url;
    shortLink.href = `${API_BASE}/${data.short_code}`;
    result.classList.remove("hidden");
    stats.classList.add("hidden");
  } catch (err) {
    showError(err.message);
  }
});

statsButton.addEventListener("click", async () => {
  if (!currentCode) {
    return;
  }
  hideError();
  try {
    renderStats(await fetchStats(currentCode));
  } catch (err) {
    showError(err.message);
  }
});

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
    throw new Error("Could not load stats for this link yet.");
  }
  return response.json();
}

function renderStats(data) {
  statsCode.textContent = data.short_code;
  statsTotal.textContent = data.total_clicks;
  statsRows.replaceChildren();
  for (const entry of data.daily) {
    const row = document.createElement("tr");
    const day = document.createElement("td");
    const count = document.createElement("td");
    day.textContent = entry.day;
    count.textContent = entry.count;
    row.append(day, count);
    statsRows.append(row);
  }
  stats.classList.remove("hidden");
}

function showError(message) {
  errorBox.textContent = message;
  errorBox.classList.remove("hidden");
}

function hideError() {
  errorBox.classList.add("hidden");
}
