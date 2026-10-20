async function loadChartData() {
  const res = await fetch("/api/chart-c.json");
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

function drawChart(canvas, payload) {
  const ctx = canvas.getContext("2d");
  const dpr = window.devicePixelRatio || 1;
  const width = canvas.clientWidth || canvas.width;
  const height = Math.round(width * 0.46);
  canvas.width = width * dpr;
  canvas.height = height * dpr;
  ctx.scale(dpr, dpr);

  const pad = { l: 52, r: 16, t: 16, b: 40 };
  const plotW = width - pad.l - pad.r;
  const plotH = height - pad.t - pad.b;

  const ohc = payload.ohc["0_2000m"].annual;
  const sst = payload.sst.annual;
  const years = ohc.map((d) => d.year);
  const ohcVals = ohc.map((d) => d.ohc_1e22j);
  const sstYears = sst.map((d) => d.year);
  const sstVals = sst.map((d) => d.anomaly_c);

  const xMin = Math.min(...years, ...sstYears);
  const xMax = Math.max(...years, ...sstYears);
  const yMin = Math.min(...ohcVals);
  const yMax = Math.max(...ohcVals);
  const sMin = Math.min(...sstVals);
  const sMax = Math.max(...sstVals);

  const xScale = (y) => pad.l + ((y - xMin) / (xMax - xMin)) * plotW;
  const yScale = (v) => pad.t + plotH - ((v - yMin) / (yMax - yMin)) * plotH;
  const yScaleSst = (v) => pad.t + plotH - ((v - sMin) / (sMax - sMin)) * plotH;

  ctx.clearRect(0, 0, width, height);
  ctx.strokeStyle = "#888";
  ctx.beginPath();
  ctx.moveTo(pad.l, pad.t);
  ctx.lineTo(pad.l, pad.t + plotH);
  ctx.lineTo(pad.l + plotW, pad.t + plotH);
  ctx.stroke();

  ctx.font = "12px system-ui, sans-serif";
  ctx.fillStyle = getComputedStyle(document.body).color;
  ctx.fillText("OHC ×10²² J", 4, pad.t + 10);
  ctx.fillText("SST °C", pad.l + plotW - 40, pad.t + 10);

  ctx.strokeStyle = "#1f77b4";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ohc.forEach((d, i) => {
    const x = xScale(d.year);
    const y = yScale(d.ohc_1e22j);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  const line = payload.ohc["0_2000m"].trends.long.trend_line || [];
  if (line.length) {
    ctx.strokeStyle = "#1f77b4";
    ctx.setLineDash([5, 4]);
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

  ctx.strokeStyle = "#ff7f0e";
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  sst.forEach((d, i) => {
    const x = xScale(d.year);
    const y = yScaleSst(d.anomaly_c);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();
}

function renderLists(payload) {
  document.getElementById("chart-note").textContent =
    "Blue: 0–2000 m ocean heat content with linear trend (dashed). Orange: global ocean SST anomaly (1901–2000 baseline).";

  document.getElementById("facts").replaceChildren(
    ...payload.facts.map((t) => {
      const li = document.createElement("li");
      li.textContent = t;
      return li;
    })
  );
  document.getElementById("read").textContent = payload.read;
  document.getElementById("sources").replaceChildren(
    ...payload.sources.map((s) => {
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.href = s.url;
      a.textContent = s.label;
      a.rel = "noopener";
      li.append(a, document.createTextNode(` — ${s.license}`));
      return li;
    })
  );
  document.getElementById("conversion-note").textContent = payload.heating_rate_citation;
}

async function main() {
  const status = document.getElementById("status");
  try {
    const data = await loadChartData();
    status.textContent = `Last complete year: ${data.last_complete_year}.`;
    drawChart(document.getElementById("chart"), data);
    renderLists(data);
  } catch (err) {
    status.textContent = `Failed to load chart data: ${err.message}`;
    status.classList.add("error");
  }
}

main();
