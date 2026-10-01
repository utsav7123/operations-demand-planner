"use strict";

const formatNumber = new Intl.NumberFormat("en-CA");
function byId(id) { return document.getElementById(id); }
function svgEl(name, attrs = {}) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", name);
  Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, String(value)));
  return node;
}
function drawForecast(container, rows) {
  const width = 820, height = 320;
  const pad = { top: 20, right: 18, bottom: 42, left: 58 };
  const plotW = width - pad.left - pad.right, plotH = height - pad.top - pad.bottom;
  const max = Math.max(...rows.map(row => row.forecast_requests));
  const x = index => pad.left + (index / Math.max(1, rows.length - 1)) * plotW;
  const y = value => pad.top + (1 - value / Math.max(1, max * 1.08)) * plotH;
  const svg = svgEl("svg", { viewBox: `0 0 ${width} ${height}`, role: "img", "aria-label": "Fourteen day demand forecast" });
  for (let i = 0; i <= 4; i += 1) {
    const value = (max * i) / 4, yPos = y(value);
    svg.appendChild(svgEl("line", { x1: pad.left, x2: width - pad.right, y1: yPos, y2: yPos, stroke: "#e4e8eb" }));
    const label = svgEl("text", { x: pad.left - 10, y: yPos + 4, "text-anchor": "end", fill: "#687480", "font-size": 11 });
    label.textContent = formatNumber.format(Math.round(value)); svg.appendChild(label);
  }
  const points = rows.map((row, index) => `${x(index)},${y(row.forecast_requests)}`).join(" ");
  svg.appendChild(svgEl("polyline", { points, fill: "none", stroke: "#0f5f73", "stroke-width": 2.5, "stroke-linejoin": "round", "stroke-linecap": "round" }));
  rows.forEach((row, index) => svg.appendChild(svgEl("circle", { cx: x(index), cy: y(row.forecast_requests), r: 3.2, fill: "#0f5f73" })));
  [0, 6, 13].forEach(index => {
    if (!rows[index]) return;
    const label = svgEl("text", { x: x(index), y: height - 14, "text-anchor": index === 0 ? "start" : index === rows.length - 1 ? "end" : "middle", fill: "#687480", "font-size": 11 });
    label.textContent = new Date(`${rows[index].date}T00:00:00`).toLocaleDateString("en-CA", { month: "short", day: "numeric" });
    svg.appendChild(label);
  });
  container.replaceChildren(svg);
}
function renderStaffing(rows) {
  const body = byId("staffing-body"), fragment = document.createDocumentFragment();
  rows.forEach(row => {
    const tr = document.createElement("tr"), gap = row.staffing_gap;
    const status = gap > 0 ? "Short" : gap < 0 ? "Capacity" : "Balanced";
    const values = [row.region, formatNumber.format(row.forecast_requests), formatNumber.format(row.required_staff), formatNumber.format(row.typical_staff), gap > 0 ? `+${gap}` : String(gap), status];
    values.forEach((value, index) => {
      const td = document.createElement("td"); td.textContent = value;
      if (index === 5) td.className = `status ${gap > 0 ? "positive" : gap < 0 ? "negative" : "neutral"}`;
      tr.appendChild(td);
    });
    fragment.appendChild(tr);
  });
  body.replaceChildren(fragment);
}
async function main() {
  const status = byId("page-status");
  try {
    const response = await fetch("../data/dashboard.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`Data request failed with ${response.status}`);
    const data = await response.json();
    drawForecast(byId("forecast-chart"), data.forecast_daily);
    renderStaffing(data.forecast_by_region);
    const totalGap = data.forecast_by_region.reduce((sum, row) => sum + row.staffing_gap, 0);
    byId("forecast-total").textContent = formatNumber.format(data.forecast_daily.reduce((sum, row) => sum + row.forecast_requests, 0));
    byId("gap-total").textContent = totalGap > 0 ? `+${formatNumber.format(totalGap)}` : formatNumber.format(totalGap);
    status.textContent = "Forecast table and staffing estimates loaded from the same generated dataset as the overview.";
  } catch (error) {
    status.textContent = "Forecast data could not be loaded.";
    status.dataset.state = "error";
  }
}
main();
