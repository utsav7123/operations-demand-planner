"use strict";

const DATA_URL = "./data/dashboard.json";
const formatNumber = new Intl.NumberFormat("en-CA");
const formatCompact = new Intl.NumberFormat("en-CA", { notation: "compact", maximumFractionDigits: 1 });
const formatPercent = new Intl.NumberFormat("en-CA", { style: "percent", maximumFractionDigits: 1 });

function byId(id) { return document.getElementById(id); }
function setText(id, value) { const node = byId(id); if (node) node.textContent = value; }
function svgEl(name, attrs = {}) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", name);
  Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, String(value)));
  return node;
}
function niceRange(values) {
  const clean = values.filter(Number.isFinite);
  const min = Math.min(...clean);
  const max = Math.max(...clean);
  if (min === max) return [Math.max(0, min - 1), max + 1];
  const padding = (max - min) * 0.08;
  return [Math.max(0, min - padding), max + padding];
}
function drawLineChart(container, series, options = {}) {
  const width = 760, height = 300;
  const pad = { top: 20, right: 16, bottom: 36, left: 54 };
  const plotW = width - pad.left - pad.right;
  const plotH = height - pad.top - pad.bottom;
  const allValues = series.flatMap(item => item.values.map(point => point.value));
  if (!allValues.length) { container.innerHTML = '<div class="chart-empty">No data available.</div>'; return; }
  const [minY, maxY] = niceRange(allValues);
  const pointCount = Math.max(...series.map(item => item.values.length));
  const x = index => pad.left + (index / Math.max(1, pointCount - 1)) * plotW;
  const y = value => pad.top + (1 - (value - minY) / Math.max(1, maxY - minY)) * plotH;
  const svg = svgEl("svg", { viewBox: `0 0 ${width} ${height}`, role: "img", "aria-label": options.label || "Line chart" });
  for (let i = 0; i <= 4; i += 1) {
    const value = minY + ((maxY - minY) * i) / 4;
    const yPos = y(value);
    svg.appendChild(svgEl("line", { x1: pad.left, x2: width - pad.right, y1: yPos, y2: yPos, stroke: "#e4e8eb", "stroke-width": 1 }));
    const label = svgEl("text", { x: pad.left - 10, y: yPos + 4, "text-anchor": "end", fill: "#687480", "font-size": 11 });
    label.textContent = options.percent ? formatPercent.format(value) : formatCompact.format(value);
    svg.appendChild(label);
  }
  series.forEach((item, seriesIndex) => {
    const points = item.values.map((point, index) => `${x(index)},${y(point.value)}`).join(" ");
    svg.appendChild(svgEl("polyline", { points, fill: "none", stroke: seriesIndex === 0 ? "#0f5f73" : "#7b8793", "stroke-width": 2.2, "stroke-linejoin": "round", "stroke-linecap": "round" }));
  });
  const labels = series[0].values;
  [0, Math.floor((labels.length - 1) / 2), labels.length - 1].forEach(index => {
    const text = svgEl("text", { x: x(index), y: height - 12, "text-anchor": index === 0 ? "start" : index === labels.length - 1 ? "end" : "middle", fill: "#687480", "font-size": 11 });
    text.textContent = new Date(`${labels[index].date}T00:00:00`).toLocaleDateString("en-CA", { month: "short", day: "numeric" });
    svg.appendChild(text);
  });
  container.replaceChildren(svg);
}
function drawBarChart(container, rows, options = {}) {
  const width = 760, rowHeight = 42;
  const height = Math.max(230, rows.length * rowHeight + 36);
  const pad = { top: 10, right: 48, bottom: 18, left: 130 };
  const plotW = width - pad.left - pad.right;
  const max = Math.max(...rows.map(row => Math.abs(row.value)), 1);
  const svg = svgEl("svg", { viewBox: `0 0 ${width} ${height}`, role: "img", "aria-label": options.label || "Bar chart" });
  rows.forEach((row, index) => {
    const y = pad.top + index * rowHeight;
    const barWidth = (Math.abs(row.value) / max) * plotW;
    const label = svgEl("text", { x: pad.left - 12, y: y + 22, "text-anchor": "end", fill: "#3d4852", "font-size": 12, "font-weight": 650 });
    label.textContent = row.label; svg.appendChild(label);
    svg.appendChild(svgEl("rect", { x: pad.left, y: y + 7, width: plotW, height: 20, rx: 4, fill: "#eef1f3" }));
    svg.appendChild(svgEl("rect", { x: pad.left, y: y + 7, width: barWidth, height: 20, rx: 4, fill: "#0f5f73" }));
    const value = svgEl("text", { x: pad.left + barWidth + 8, y: y + 22, fill: "#3d4852", "font-size": 12, "font-weight": 700 });
    value.textContent = options.percent ? formatPercent.format(row.value) : formatNumber.format(row.value);
    svg.appendChild(value);
  });
  container.replaceChildren(svg);
}
function renderRegionTable(rows) {
  const body = byId("region-table-body");
  if (!body) return;
  const fragment = document.createDocumentFragment();
  rows.forEach(row => {
    const tr = document.createElement("tr");
    const values = [row.region, formatNumber.format(row.incoming_requests), formatPercent.format(row.completion_rate), formatPercent.format(row.sla_rate), formatPercent.format(row.quality_rate), row.avg_resolution_hours.toFixed(2)];
    values.forEach(value => { const td = document.createElement("td"); td.textContent = value; tr.appendChild(td); });
    fragment.appendChild(tr);
  });
  body.replaceChildren(fragment);
}
function renderInsights(data) {
  const list = byId("insight-list");
  if (!list) return;
  const worstGap = [...data.forecast_by_region].sort((a, b) => b.staffing_gap - a.staffing_gap)[0];
  const bestSla = [...data.regions].sort((a, b) => b.sla_rate - a.sla_rate)[0];
  const exception = data.exceptions[0];
  const items = [
    ["Capacity", `${worstGap.region} has the largest forecast staffing gap across the next 14 days.`],
    ["Service level", `${bestSla.region} has the strongest overall SLA attainment in the generated history.`],
    ["Exception", exception ? `${exception.region} / ${exception.user_profile} recorded the strongest demand spike in the anomaly list.` : "No demand spikes were flagged."]
  ];
  const fragment = document.createDocumentFragment();
  items.forEach(([title, message]) => {
    const li = document.createElement("li"), strong = document.createElement("strong"), span = document.createElement("span");
    strong.textContent = title; span.textContent = message; li.append(strong, span); fragment.appendChild(li);
  });
  list.replaceChildren(fragment);
}
async function loadDashboard() {
  const status = byId("dashboard-status");
  try {
    const response = await fetch(DATA_URL, { cache: "no-store" });
    if (!response.ok) throw new Error(`Dashboard data request failed with ${response.status}`);
    const data = await response.json();
    setText("metric-incoming", formatNumber.format(data.overall.incoming_requests));
    setText("metric-completion", formatPercent.format(data.overall.completion_rate));
    setText("metric-sla", formatPercent.format(data.overall.sla_rate));
    setText("metric-backlog", formatNumber.format(data.overall.current_backlog));
    setText("data-through", new Date(`${data.overall.date_through}T00:00:00`).toLocaleDateString("en-CA", { year: "numeric", month: "short", day: "numeric" }));
    const history = data.history;
    drawLineChart(byId("volume-chart"), [
      { values: history.map(row => ({ date: row.date, value: row.incoming })) },
      { values: history.map(row => ({ date: row.date, value: row.completed })) }
    ], { label: "Daily incoming and completed requests over the last 90 days" });
    drawLineChart(byId("service-chart"), [
      { values: history.map(row => ({ date: row.date, value: row.sla_rate })) },
      { values: history.map(row => ({ date: row.date, value: row.quality_rate })) }
    ], { label: "Daily SLA and quality rates over the last 90 days", percent: true });
    drawBarChart(byId("regional-chart"), data.regions.map(row => ({ label: row.region, value: row.incoming_requests })), { label: "Total incoming requests by region" });
    renderRegionTable(data.regions);
    renderInsights(data);
    if (status) { status.textContent = `Loaded reproducible sample data through ${data.overall.date_through}.`; status.dataset.state = "ready"; }
  } catch (error) {
    if (status) { status.textContent = "The dashboard data could not be loaded. The analysis code and generated data are still available in the repository."; status.dataset.state = "error"; }
  }
}
loadDashboard();
