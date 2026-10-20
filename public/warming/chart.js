const COLORS = ["#1f77b4", "#d62728", "#2ca02c"];

async function loadChartData() {
  const res = await fetch("/api/chart-a.json");
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

function drawChart(canvas, payload) {
  const ctx = canvas.getContext("2d");
  const dpr = window.devicePixelRatio || 1;
  const width = canvas.clientWidth || canvas.width;
  const height = Math.round(width * 0.5);
  canvas.width = width * dpr;
  canvas.height = height * dpr;
  ctx.scale(dpr, dpr);

  const pad = { l: 52, r: 16, t: 16, b: 40 };
  const plotW = width - pad.l - pad.r;
  const plotH = height - pad.t - pad.b;

  const allYears = [];
  const allVals = [];
  payload.series.forEach((s) => {
    s.annual.forEach((p) => {
      allYears.push(p.year);
      allVals.push(p.anomaly_c);
    });
  });
  const xMin = Math.min(...allYears);
  const xMax = Math.max(...allYears);
  let yMin = Math.min(...allVals);
  let yMax = Math.max(...allVals);
  const yPad = (yMax - yMin) * 0.08 || 0.2;
  yMin -= yPad;
  yMax += yPad;

  const xScale = (y) => pad.l + ((y - xMin) / (xMax - xMin)) * plotW;
  const yScale = (v) => pad.t + plotH - ((v - yMin) / (yMax - yMin)) * plotH;

  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = getComputedStyle(document.body).color;
  ctx.strokeStyle = "#888";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(pad.l, pad.t);
  ctx.lineTo(pad.l, pad.t + plotH);
  ctx.lineTo(pad.l + plotW, pad.t + plotH);
  ctx.stroke();

  ctx.font = "12px system-ui, sans-serif";
  ctx.fillText("°C anomaly", 4, pad.t + 12);
  ctx.fillText(String(xMin), pad.l, height - 8);
  ctx.fillText(String(xMax), pad.l + plotW - 24, height - 8);

  payload.series.forEach((series, idx) => {
    const color = COLORS[idx % COLORS.length];
    const annual = series.annual.filter((p) => p.year >= 1970);
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    annual.forEach((p, i) => {
      const x = xScale(p.year);
      const y = yScale(p.anomaly_c);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    const line = series.trend_lines?.from_1970 || [];
    if (line.length > 1) {
      ctx.fillStyle = color + "33";
      ctx.beginPath();
      line.forEach((p, i) => {
        const x = xScale(p.year);
        const yLo = yScale(p.band_low_c);
        const yHi = yScale(p.band_high_c);
        if (i === 0) {
          ctx.moveTo(x, yLo);
        } else {
          ctx.lineTo(x, yLo);
        }
      });
      for (let i = line.length - 1; i >= 0; i--) {
        const x = xScale(line[i].year);
        const yHi = yScale(line[i].band_high_c);
        ctx.lineTo(x, yHi);
      }
      ctx.closePath();
      ctx.fill();

      ctx.strokeStyle = color;
      ctx.setLineDash([6, 4]);
      ctx.lineWidth = 2;
      ctx.beginPath();
      line.forEach((p, i) => {
        const x = xScale(p.year);
        const y = yScale(p.trend_c);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.stroke();
      ctx.setLineDash([]);
    }
  });
}

function renderLists(payload) {
  const bandLabel =
    payload.series[0]?.trend_lines?.band_label ||
    "95% trend uncertainty (AR(1)-adjusted OLS fit)";
  document.getElementById("baseline-note").textContent =
    `Baseline: ${payload.baseline.label} (${payload.baseline.start_year}–${payload.baseline.end_year}). ` +
    `${payload.baseline.method} Dashed lines: linear trends since 1970; shaded bands: ${bandLabel}.`;

  const facts = document.getElementById("facts");
  facts.replaceChildren(...payload.facts.map((t) => {
    const li = document.createElement("li");
    li.textContent = t;
    return li;
  }));

  document.getElementById("read").textContent = payload.read;

  const sources = document.getElementById("sources");
  sources.replaceChildren(
    ...payload.series.map((s) => {
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.href = s.url;
      a.textContent = s.label;
      a.rel = "noopener";
      li.append(a, document.createTextNode(` — ${s.license}`));
      return li;
    })
  );
}

async function main() {
  const status = document.getElementById("status");
  try {
    const data = await loadChartData();
    const asOf = data.data_as_of?.label;
    const years = data.series.map((s) => s.last_complete_year ?? s.data_as_of_year).join(", ");
    status.textContent = asOf
      ? `${asOf} (series years: ${years}).`
      : `Last complete year: ${years} (per series).`;
    drawChart(document.getElementById("chart"), data);
    renderLists(data);
  } catch (err) {
    status.textContent = `Failed to load chart data: ${err.message}`;
    status.classList.add("error");
  }
}

main();
