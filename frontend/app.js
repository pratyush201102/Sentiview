const state = {
  activeSearchId: null,
  distributionChart: null,
  trendChart: null,
  loading: false,
  historySkip: 0,
  historyLimit: 10,
  historyTotal: 0,
  historyHasMore: false,
};

const REQUEST_TIMEOUT_MS = 20000;

const chartColors = {
  positive: "#16a34a",
  neutral: "#64748b",
  negative: "#dc2626",
  muted: "#cbd5e1",
};

const exportColumns = [
  "source_post_id",
  "author",
  "subreddit",
  "title",
  "body",
  "permalink",
  "posted_at",
  "neg_score",
  "neu_score",
  "pos_score",
  "compound_score",
  "sentiment_label",
];

const centerTextPlugin = {
  id: "centerText",
  afterDraw(chart, _args, pluginOptions) {
    if (!pluginOptions || !pluginOptions.enabled) {
      return;
    }

    const { ctx, chartArea } = chart;
    if (!chartArea) {
      return;
    }

    const centerX = (chartArea.left + chartArea.right) / 2;
    const centerY = (chartArea.top + chartArea.bottom) / 2;

    ctx.save();
    ctx.textAlign = "center";
    ctx.fillStyle = "#0f172a";
    ctx.font = "700 24px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
    ctx.fillText(String(pluginOptions.mainText ?? ""), centerX, centerY - 4);

    ctx.fillStyle = "#64748b";
    ctx.font = "500 12px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
    ctx.fillText(String(pluginOptions.subText ?? ""), centerX, centerY + 16);
    ctx.restore();
  },
};

const el = {
  dashboardRoot: document.getElementById("dashboardRoot"),
  apiBase: document.getElementById("apiBase"),
  analyzeForm: document.getElementById("analyzeForm"),
  keyword: document.getElementById("keyword"),
  limit: document.getElementById("limit"),
  analyzeBtn: document.getElementById("analyzeBtn"),
  exportBtn: document.getElementById("exportBtn"),
  exportColumns: document.getElementById("exportColumns"),
  status: document.getElementById("status"),
  historyMeta: document.getElementById("historyMeta"),
  historyPrevBtn: document.getElementById("historyPrevBtn"),
  historyNextBtn: document.getElementById("historyNextBtn"),
  historyPageInfo: document.getElementById("historyPageInfo"),
  historyBody: document.getElementById("historyBody"),
  mKeyword: document.getElementById("mKeyword"),
  mFetched: document.getElementById("mFetched"),
  mAnalyzed: document.getElementById("mAnalyzed"),
  mPositive: document.getElementById("mPositive"),
  mNeutral: document.getElementById("mNeutral"),
  mNegative: document.getElementById("mNegative"),
  distributionCanvas: document.getElementById("distributionChart"),
  trendCanvas: document.getElementById("trendChart"),
  distributionCard: document.getElementById("distributionCard"),
  trendCard: document.getElementById("trendCard"),
  historyCard: document.getElementById("historyCard"),
};

function toLabel(columnName) {
  return columnName
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function initExportColumns() {
  if (!el.exportColumns) {
    return;
  }

  el.exportColumns.innerHTML = "";

  exportColumns.forEach((column) => {
    const item = document.createElement("label");
    item.className = "export-column-item";

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.value = column;
    checkbox.checked = true;

    const text = document.createElement("span");
    text.textContent = toLabel(column);

    item.appendChild(checkbox);
    item.appendChild(text);
    el.exportColumns.appendChild(item);
  });
}

function getSelectedExportColumns() {
  if (!el.exportColumns) {
    return exportColumns;
  }

  const selected = Array.from(el.exportColumns.querySelectorAll('input[type="checkbox"]:checked'))
    .map((input) => input.value)
    .filter((column) => exportColumns.includes(column));

  return selected;
}

function getApiBase() {
  return el.apiBase.value.trim().replace(/\/$/, "");
}

function getApiRoot() {
  const base = getApiBase();
  if (base.endsWith("/api/v1")) {
    return base.slice(0, -7);
  }
  return base;
}

function parseErrorMessage(payload, fallback) {
  if (!payload) {
    return fallback;
  }

  if (typeof payload === "string") {
    return payload;
  }

  if (payload.detail) {
    return typeof payload.detail === "string" ? payload.detail : JSON.stringify(payload.detail);
  }

  return fallback;
}

function setLoading(isLoading) {
  state.loading = isLoading;
  el.dashboardRoot.classList.toggle("loading", isLoading);

  [el.distributionCard, el.trendCard, el.historyCard].forEach((card) => {
    card.classList.toggle("card-loading", isLoading);
  });

  el.analyzeBtn.disabled = isLoading;
  updateHistoryControls();
}

function setStatus(message, isError = false) {
  el.status.textContent = message;
  el.status.style.color = isError ? "#b91c1c" : "#0f172a";
  // Hide the status element when showing the default "Dashboard ready" message
  if (!isError && message === "Dashboard ready.") {
    el.status.style.visibility = "hidden";
    el.status.style.margin = "0";
    el.status.style.height = "0";
    el.status.style.padding = "0";
  } else {
    el.status.style.visibility = "visible";
    el.status.style.margin = "";
    el.status.style.height = "";
    el.status.style.padding = "";
  }
}

async function checkBackendHealth() {
  const response = await fetch(`${getApiRoot()}/health`);
  if (!response.ok) {
    throw new Error("API health check failed");
  }

  return response.json();
}

async function request(path, options = {}) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  let response;

  try {
    response = await fetch(`${getApiBase()}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
      ...options,
      signal: controller.signal,
    });
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error("Request timed out. Please try again.");
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }

  if (!response.ok) {
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      const payload = await response.json();
      throw new Error(parseErrorMessage(payload, `Request failed (${response.status})`));
    }

    const payload = await response.text();
    throw new Error(parseErrorMessage(payload, `Request failed (${response.status})`));
  }

  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return response.json();
  }

  return response;
}

function updateSummary(search) {
  el.mKeyword.textContent = search.keyword;
  el.mFetched.textContent = String(search.fetched_count);
  el.mAnalyzed.textContent = String(search.analyzed_count);
  el.mPositive.textContent = String(search.positive_count);
  el.mNeutral.textContent = String(search.neutral_count);
  el.mNegative.textContent = String(search.negative_count);
}

function clearSummary() {
  updateSummary({
    keyword: "-",
    fetched_count: 0,
    analyzed_count: 0,
    positive_count: 0,
    neutral_count: 0,
    negative_count: 0,
  });
}

function formatPercent(value, total) {
  if (!total) {
    return "0.0";
  }

  return ((value / total) * 100).toFixed(1);
}

function truncateLabel(text, maxLength = 18) {
  if (!text || text.length <= maxLength) {
    return text;
  }
  return `${text.slice(0, maxLength - 1)}…`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function safeText(value, fallback = "") {
  const text = typeof value === "string" ? value.trim() : "";
  if (!text || text.toLowerCase() === "undefined" || text.toLowerCase() === "null") {
    return fallback;
  }
  return text;
}

function renderDistributionChart(search) {
  if (state.distributionChart) {
    state.distributionChart.destroy();
  }

  const sentimentLabels = ["Positive", "Neutral", "Negative"];
  const values = [
    Number(search.positive_count ?? 0),
    Number(search.neutral_count ?? 0),
    Number(search.negative_count ?? 0),
  ].map((value) => (Number.isFinite(value) && value > 0 ? value : 0));
  const total = values.reduce((sum, value) => sum + value, 0);
  const hasData = total > 0;

  state.distributionChart = new Chart(el.distributionCanvas, {
    type: "doughnut",
    plugins: [centerTextPlugin],
    data: {
      labels: sentimentLabels,
      datasets: [
        {
          data: hasData ? values : [1],
          backgroundColor: hasData
            ? [chartColors.positive, chartColors.neutral, chartColors.negative]
            : [chartColors.muted],
          borderColor: "#ffffff",
          borderWidth: 2,
          hoverOffset: 8,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "62%",
      plugins: {
        centerText: {
          enabled: true,
          mainText: hasData ? total : 0,
          subText: "analyzed posts",
        },
        legend: {
          display: false,
        },
        tooltip: {
          callbacks: {
            label: (context) => {
              if (!hasData) {
                return "No analyzed posts";
              }
              const value = Number(context.raw || 0);
              const chartLabel = Array.isArray(context.chart?.data?.labels)
                ? context.chart.data.labels[context.dataIndex]
                : "";
              const label =
                safeText(context.label) ||
                safeText(chartLabel) ||
                safeText(sentimentLabels[Number(context.dataIndex)]) ||
                "Sentiment";
              return `${label}: ${value} (${formatPercent(value, total)}%)`;
            },
          },
        },
      },
    },
  });
}

function toSentimentLabel(score) {
  if (score > 0.05) {
    return "positive";
  }
  if (score < -0.05) {
    return "negative";
  }
  return "neutral";
}

function buildTemporalSeries(results, maxPoints = 24) {
  const withTimestamps = results
    .filter((item) => item.posted_at)
    .map((item) => {
      const timestamp = new Date(item.posted_at);
      const score = Number(item.compound_score);
      return {
        timestamp,
        score,
      };
    })
    .filter((item) => Number.isFinite(item.score) && !Number.isNaN(item.timestamp.getTime()))
    .sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());

  if (withTimestamps.length === 0) {
    return [];
  }

  if (withTimestamps.length <= maxPoints) {
    return withTimestamps;
  }

  const bucketSize = Math.ceil(withTimestamps.length / maxPoints);
  const series = [];

  for (let i = 0; i < withTimestamps.length; i += bucketSize) {
    const bucket = withTimestamps.slice(i, i + bucketSize);
    if (bucket.length === 0) {
      continue;
    }
    const avgScore = bucket.reduce((sum, point) => sum + point.score, 0) / bucket.length;
    series.push({
      timestamp: bucket[bucket.length - 1].timestamp,
      score: avgScore,
    });
  }

  return series;
}

function renderTrendChart(results, keyword = "") {
  const series = buildTemporalSeries(Array.isArray(results) ? results : []);
  const hasData = series.length > 0;
  const labels = hasData
    ? series.map((point) => point.timestamp.toLocaleString([], { dateStyle: "short", timeStyle: "short" }))
    : ["No timestamped posts"];
  const data = hasData ? series.map((point) => Number(point.score.toFixed(4))) : [0];

  if (state.trendChart) {
    state.trendChart.destroy();
  }

  state.trendChart = new Chart(el.trendCanvas, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Compound sentiment",
          data,
          borderColor: "#0ea5e9",
          backgroundColor: "rgba(14, 165, 233, 0.15)",
          borderWidth: 2,
          pointRadius: hasData ? 3 : 0,
          pointHoverRadius: 5,
          tension: 0.3,
          fill: true,
        },
        {
          label: "Neutral baseline",
          data: labels.map(() => 0),
          borderColor: "rgba(100, 116, 139, 0.75)",
          borderDash: [5, 4],
          borderWidth: 1,
          pointRadius: 0,
          tension: 0,
          fill: false,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false,
      },
      scales: {
        x: {
          ticks: {
            autoSkip: true,
            maxTicksLimit: 7,
            maxRotation: 0,
          },
          grid: {
            display: false,
          },
        },
        y: {
          min: -1,
          max: 1,
          ticks: {
            callback: (value) => Number(value).toFixed(2),
          },
          grid: {
            color: "#e2e8f0",
          },
        },
      },
      plugins: {
        legend: {
          position: "bottom",
        },
        tooltip: {
          callbacks: {
            title: (items) => {
              if (!hasData || items.length === 0) {
                return "No temporal sentiment data";
              }
              const index = items[0].dataIndex;
              const point = series[index];
              if (!point) {
                return "Sentiment point";
              }
              const chartKeyword = safeText(keyword, "Search");
              return `${chartKeyword} · ${point.timestamp.toLocaleString()}`;
            },
            footer: (items) => {
              if (!hasData || items.length === 0) {
                return "";
              }
              const score = Number(items[0].parsed.y || 0);
              const label = toSentimentLabel(score);
              return `Sentiment: ${label} (${score.toFixed(3)})`;
            },
          },
        },
      },
    },
  });
}

function renderHistory(searches) {
  el.historyBody.innerHTML = "";

  if (!Array.isArray(searches) || searches.length === 0) {
    const emptyRow = document.createElement("tr");
    emptyRow.innerHTML = '<td colspan="6">No searches yet. Run an analysis to populate history.</td>';
    el.historyBody.appendChild(emptyRow);
    return;
  }

  searches.forEach((item) => {
    const row = document.createElement("tr");
    row.tabIndex = 0;
    row.setAttribute("role", "button");
    row.setAttribute("aria-label", `Load search ${item.keyword}`);
    if (item.id === state.activeSearchId) {
      row.classList.add("selected");
    }

    row.innerHTML = `
      <td>${escapeHtml(item.keyword)}</td>
      <td>${escapeHtml(new Date(item.created_at).toLocaleString())}</td>
      <td>${escapeHtml(item.analyzed_count)}</td>
      <td>${escapeHtml(item.positive_count)}</td>
      <td>${escapeHtml(item.neutral_count)}</td>
      <td>${escapeHtml(item.negative_count)}</td>
    `;

    row.addEventListener("click", async () => {
      await loadSearch(item.id);
    });

    row.addEventListener("keydown", async (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        await loadSearch(item.id);
      }
    });

    el.historyBody.appendChild(row);
  });
}

function updateHistoryControls() {
  const currentPage = Math.floor(state.historySkip / state.historyLimit) + 1;
  const totalPages = Math.max(1, Math.ceil(state.historyTotal / state.historyLimit));
  el.historyPageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
  el.historyPrevBtn.disabled = state.historySkip === 0 || state.loading;
  el.historyNextBtn.disabled = !state.historyHasMore || state.loading;
}

async function loadSearch(searchId) {
  try {
    setLoading(true);
    const payload = await request(`/searches/${searchId}`);
    state.activeSearchId = payload.search.id;
    el.exportBtn.disabled = false;

    updateSummary(payload.search);
    renderDistributionChart(payload.search);
    renderTrendChart(payload.results, payload.search.keyword);
    setStatus(`Loaded search: ${safeText(payload.search.keyword, "Untitled")}`);
  } finally {
    setLoading(false);
  }
}

async function loadHistory() {
  const payload = await request(`/searches?skip=${state.historySkip}&limit=${state.historyLimit}`);
  const searches = Array.isArray(payload.items) ? payload.items : [];
  const total = Number(payload.total || 0);

  state.historyTotal = total;
  state.historyHasMore = Boolean(payload.has_more);

  const startIndex = total > 0 ? state.historySkip + 1 : 0;
  const endIndex = state.historySkip + searches.length;
  el.historyMeta.textContent = `Showing ${startIndex}-${endIndex} of ${total} searches`;
  updateHistoryControls();
  renderHistory(searches);

  if (searches.length === 0) {
    state.activeSearchId = null;
    el.exportBtn.disabled = true;
    clearSummary();
    renderDistributionChart({ positive_count: 0, neutral_count: 0, negative_count: 0 });
    renderTrendChart([]);
    setStatus("No search history yet. Run your first analysis.");
    return;
  }

  if (!searches.some((item) => item.id === state.activeSearchId)) {
    state.activeSearchId = null;
  }

  if (!state.activeSearchId) {
    await loadSearch(searches[0].id);
    return;
  }

  renderHistory(searches);
}

async function bootDashboard() {
  try {
    setLoading(true);
    const health = await checkBackendHealth();
    if (health.database === "down") {
      setStatus(
        "Database is down. Start PostgreSQL (e.g., docker compose up -d) and refresh.",
        true
      );
      return;
    }

    await loadHistory();
    setStatus("Dashboard ready.");
  } catch (error) {
    setStatus(`Initial load failed: ${error.message}`, true);
  } finally {
    setLoading(false);
  }
}

async function handleAnalyze(event) {
  event.preventDefault();
  const keyword = el.keyword.value.trim();
  const limit = Number(el.limit.value);

  if (!keyword || !Number.isInteger(limit)) {
    setStatus("Provide a valid keyword and limit.", true);
    return;
  }

  setLoading(true);
  setStatus("Analyzing keyword...");

  try {
    const payload = await request("/analyze", {
      method: "POST",
      body: JSON.stringify({
        keyword,
        source: "reddit",
        limit,
      }),
    });

    state.activeSearchId = payload.search.id;
    el.exportBtn.disabled = false;
    state.historySkip = 0;

    updateSummary(payload.search);
    renderDistributionChart(payload.search);
    renderTrendChart(payload.results, payload.search.keyword);
    await loadHistory();

    if (payload.search.analyzed_count === 0) {
      setStatus("Analysis completed, but no analyzable text was found in the fetched posts.");
    } else {
      setStatus(`Analysis complete: ${payload.search.analyzed_count} posts analyzed.`);
    }
  } catch (error) {
    setStatus(`Analyze failed: ${error.message}`, true);
  } finally {
    setLoading(false);
  }
}

function handleExport() {
  if (!state.activeSearchId) {
    return;
  }

  const selectedColumns = getSelectedExportColumns();
  if (selectedColumns.length === 0) {
    setStatus("Select at least one column for CSV export.", true);
    return;
  }

  const query = new URLSearchParams({ columns: selectedColumns.join(",") }).toString();

  const link = document.createElement("a");
  link.href = `${getApiBase()}/searches/${state.activeSearchId}/export.csv?${query}`;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.click();
}

async function handleHistoryPrevious() {
  if (state.loading || state.historySkip === 0) {
    return;
  }
  state.historySkip = Math.max(0, state.historySkip - state.historyLimit);
  await loadHistory();
}

async function handleHistoryNext() {
  if (state.loading || !state.historyHasMore) {
    return;
  }
  state.historySkip += state.historyLimit;
  await loadHistory();
}

el.analyzeForm.addEventListener("submit", handleAnalyze);
el.exportBtn.addEventListener("click", handleExport);
el.historyPrevBtn.addEventListener("click", handleHistoryPrevious);
el.historyNextBtn.addEventListener("click", handleHistoryNext);

initExportColumns();
bootDashboard();
