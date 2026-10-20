const CHARTS = [
  {
    key: "a",
    href: "/warming/",
    title: "Is global warming speeding up?",
    api: "/api/chart-a.json",
  },
  {
    key: "b",
    href: "/airborne/",
    title: "Is the airborne fraction rising?",
    api: "/api/chart-b.json",
  },
  {
    key: "c",
    href: "/ocean/",
    title: "Where is the heat going?",
    api: "/api/chart-c.json",
  },
];

async function loadJson(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  return res.json();
}

function cardElement(chart, payload) {
  const li = document.createElement("li");
  li.className = "chart-card";
  const h2 = document.createElement("h2");
  const link = document.createElement("a");
  link.href = chart.href;
  link.textContent = chart.title;
  h2.append(link);
  const read = document.createElement("p");
  read.className = "read-snippet";
  read.textContent = payload?.read || "(No summary yet.)";
  const meta = document.createElement("p");
  meta.className = "meta";
  const label = payload?.data_as_of?.label;
  meta.textContent = label ? `${label}. ` : "";
  meta.append(document.createTextNode(`Open chart ${chart.key} →`));
  const chartLink = document.createElement("a");
  chartLink.href = chart.href;
  chartLink.textContent = chart.href;
  chartLink.className = "sr-only";
  li.append(h2, read, meta);
  return li;
}

async function main() {
  const status = document.getElementById("status");
  const cards = document.getElementById("cards");
  try {
    const payloads = await Promise.all(
      CHARTS.map(async (c) => {
        try {
          return await loadJson(c.api);
        } catch {
          return null;
        }
      })
    );
    cards.replaceChildren(
      ...CHARTS.map((c, i) => cardElement(c, payloads[i]))
    );
    status.textContent = "Summaries from latest published chart aggregates.";
  } catch (err) {
    status.textContent = `Failed to load dashboard: ${err.message}`;
    status.classList.add("error");
  }
}

main();
