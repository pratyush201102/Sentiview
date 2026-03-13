const state = {
  activeSearchId: null,
  distributionChart: null,
  trendChart: null,
};

const chartColors = {
  positive: "#16a34a",
  neutral: "#64748b",
  negative: "#dc2626",
  muted: "#cbd5e1",
};

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
  apiBase: document.getElementById("apiBase"),
  analyzeForm: document.getElementById("analyzeForm"),
  keyword: document.getElementById("keyword"),
  limit: document.getElementById("limit"),
  analyzeBtn: document.getElementById("analyzeBtn"),
  exportBtn: document.getElementById("exportBtn"),
  status: document.getElementById("status"),
  historyBody: document.getElementById("historyBody"),
  mKeyword: document.getElementById("mKeyword"),
  mFetched: document.getElementById("mFetched"),
  mAnalyzed: document.getElementById("mAnalyzed"),
  mPositive: document.getElementById("mPositive"),
  mNeutral: document.getElementById("mNeutral"),
  mNegative: document.getElementById("mNegative"),
  distributionCanvas: document.getElementById("distributionChart"),
  trendCanvas: document.getElementById("trendChart"),
};

function getApiBase() {
  return el.apiBase.value.trim().replace(/\/$/, "");
}

function setStatus(message, isError = false) {
  el.status.textContent = message;
  el.status.style.color = isError ? "#b91c1c" : "#0f172a";
}

async function checkBackendHealth() {
  const response = await fetch(`${getApiBase().replace(/\/api\/v1$/, "")}/health`);
  if (!response.ok) {
    throw new Error("API health check failed");
  }

  return response.json();
}

async function request(path, options = {}) {
  const response = await fetch(`${getApiBase()}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const payload = await response.text();
    throw new Error(payload || `Request failed (${response.status})`);
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

function renderDistributionChart(search) {
  if (state.distributionChart) {
    state.distributionChart.destroy();
  }

  const values = [search.positive_count, search.neutral_count, search.negative_count];
  const total = values.reduce((sum, value) => sum + value, 0);
  const hasData = total > 0;

  state.distributionChart = new Chart(el.distributionCanvas, {
    type: "doughnut",
    plugins: [centerTextPlugin],
    data: {
      labels: ["Positive", "Neutral", "Negative"],
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
          position: "bottom",
          labels: {
            filter: (item) => hasData || item.text === "No Data",
            generateLabels: (chart) => {
              if (!hasData) {
                return [
                  {
                    text: "No Data",
                    fillStyle: chartColors.muted,
                    strokeStyle: chartColors.muted,
                    lineWidth: 0,
                    hidden: false,
                    index: 0,
                  },
                ];
              }
              return Chart.defaults.plugins.legend.labels.generateLabels(chart);
            },
          },
        },
        tooltip: {
          callbacks: {
            label: (context) => {
              if (!hasData) {
                return "No analyzed posts";
              }
              const value = Number(context.raw || 0);
              return `${context.label}: ${value} (${formatPercent(value, total)}%)`;
            },
          },
        },
      },
    },
  });
}

function renderTrendChart(searches) {
  const slice = searches.slice(0, 8).reverse();
  const hasData = slice.length > 0;
  const labels = hasData
    ? slice.map((item) => [truncateLabel(item.keyword, 14), new Date(item.created_at).toLocaleDateString()])
    : ["No data"];

  const positiveData = hasData ? slice.map((item) => item.positive_count) : [0];
  const neutralData = hasData ? slice.map((item) => item.neutral_count) : [0];
  const negativeData = hasData ? slice.map((item) => item.negative_count) : [0];

  if (state.trendChart) {
    state.trendChart.destroy();
  }

  state.trendChart = new Chart(el.trendCanvas, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Positive",
          data: positiveData,
          backgroundColor: chartColors.positive,
          stack: "sentiment",
          borderRadius: 6,
        },
        {
          label: "Neutral",
          data: neutralData,
          backgroundColor: chartColors.neutral,
          stack: "sentiment",
          borderRadius: 6,
        },
        {
          label: "Negative",
          data: negativeData,
          backgroundColor: chartColors.negative,
          stack: "sentiment",
          borderRadius: 6,
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
          stacked: true,
          ticks: {
            autoSkip: false,
            maxRotation: 0,
            minRotation: 0,
          },
          grid: {
            display: false,
          },
        },
        y: {
          stacked: true,
          beginAtZero: true,
          ticks: { precision: 0 },
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
                return "No search history";
              }
              const index = items[0].dataIndex;
              const item = slice[index];
              return `${item.keyword} · ${new Date(item.created_at).toLocaleString()}`;
            },
            footer: (items) => {
              if (!hasData || items.length === 0) {
                return "";
              }
              const totalForSearch = items.reduce((sum, point) => sum + Number(point.parsed.y || 0), 0);
              return `Total analyzed: ${totalForSearch}`;
            },
          },
        },
      },
    },
  });
}

function renderHistory(searches) {
  el.historyBody.innerHTML = "";

  searches.forEach((item) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${item.keyword}</td>
      <td>${new Date(item.created_at).toLocaleString()}</td>
      <td>${item.analyzed_count}</td>
      <td>${item.positive_count}</td>
      <td>${item.neutral_count}</td>
      <td>${item.negative_count}</td>
    `;

    row.addEventListener("click", async () => {
      await loadSearch(item.id);
    });

    el.historyBody.appendChild(row);
  });
}

async function loadSearch(searchId) {
  const payload = await request(`/searches/${searchId}`);
  state.activeSearchId = payload.search.id;
  el.exportBtn.disabled = false;

  updateSummary(payload.search);
  renderDistributionChart(payload.search);
  setStatus(`Loaded search: ${payload.search.keyword}`);
}

async function loadHistory() {
  const searches = await request("/searches");
  renderHistory(searches);
  renderTrendChart(searches);

  if (searches.length > 0 && !state.activeSearchId) {
    await loadSearch(searches[0].id);
  }
}

async function bootDashboard() {
  try {
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

  el.analyzeBtn.disabled = true;
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

    updateSummary(payload.search);
    renderDistributionChart(payload.search);
    await loadHistory();

    setStatus(`Analysis complete: ${payload.search.analyzed_count} posts analyzed.`);
  } catch (error) {
    setStatus(`Analyze failed: ${error.message}`, true);
  } finally {
    el.analyzeBtn.disabled = false;
  }
}

function handleExport() {
  if (!state.activeSearchId) {
    return;
  }

  const link = document.createElement("a");
  link.href = `${getApiBase()}/searches/${state.activeSearchId}/export.csv`;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.click();
}

el.analyzeForm.addEventListener("submit", handleAnalyze);
el.exportBtn.addEventListener("click", handleExport);

bootDashboard();
