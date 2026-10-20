async function loadChartData() {
  const res = await fetch("/api/chart-b.json");
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

function drawChart(canvas, payload) {
  const ctx = canvas.getContext("2d");
  const dpr = window.devicePixelRatio || 1;
  const width = canvas.clientWidth || canvas.width;
  const height = Math.round(width * 0.44);
  canvas.width = width * dpr;
  canvas.height = height * dpr;
  ctx.scale(dpr, dpr);

  const pad = { l: 48, r: 16, t: 16, b: 40 };
  const plotW = width - pad.l - pad.r;
  const plotH = height - pad.t - pad.b;
  const annual = payload.annual;
  const years = annual.map((d) => d.year);
  const af = annual.map((d) => d.airborne_fraction);
  const smooth = annual.map((d) => d.airborne_fraction_smoothed_10y);
  const fossil = annual.map((d) => d.airborne_fraction_fossil_only);

  const xMin = Math.min(...years);
  const xMax = Math.max(...years);
  let yMin = Math.min(...af, ...fossil.filter(Boolean));
  let yMax = Math.max(...af, ...fossil.filter(Boolean));
  const yPad = (yMax - yMin) * 0.1 || 0.05;
  yMin = Math.max(0, yMin - yPad);
  yMax = Math.min(1, yMax + yPad);

  const xScale = (y) => pad.l + ((y - xMin) / (xMax - xMin)) * plotW;
  const yScale = (v) => pad.t + plotH - ((v - yMin) / (yMax - yMin)) * plotH;

  ctx.clearRect(0, 0, width, height);
  ctx.strokeStyle = "#888";
  ctx.beginPath();
  ctx.moveTo(pad.l, pad.t);
  ctx.lineTo(pad.l, pad.t + plotH);
  ctx.lineTo(pad.l + plotW, pad.t + plotH);
  ctx.stroke();

  ctx.font = "12px system-ui, sans-serif";
  ctx.fillStyle = getComputedStyle(document.body).color;
  ctx.fillText("AF", 8, pad.t + 10);

  ctx.strokeStyle = "#1f77b433";
  ctx.lineWidth = 8;
  ctx.beginPath();
  fossil.forEach((v, i) => {
    const x = xScale(years[i]);
    const y = yScale(v);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  ctx.strokeStyle = "#1f77b4";
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  af.forEach((v, i) => {
    const x = xScale(years[i]);
    const y = yScale(v);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  ctx.strokeStyle = "#d62728";
  ctx.lineWidth = 2.5;
  ctx.beginPath();
  let started = false;
  smooth.forEach((v, i) => {
    if (v == null) return;
    const x = xScale(years[i]);
    const y = yScale(v);
    if (!started) {
      ctx.moveTo(x, y);
      started = true;
    } else ctx.lineTo(x, y);
  });
  ctx.stroke();
}

function renderLists(payload) {
  document.getElementById("chart-note").textContent =
    `Annual airborne fraction (blue), fossil-only denominator (wide blue), ` +
    `${payload.smoothing.window_years}-year centered mean (red). ` +
    `Land-use emission uncertainty ±0.7 GtC/yr (1σ) is cited in facts.`;

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
  document.getElementById("conversion-note").textContent =
    `${payload.ppm_to_gtc_citation} Factor used: ${payload.ppm_to_gtc_factor} GtC per ppm.`;
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
