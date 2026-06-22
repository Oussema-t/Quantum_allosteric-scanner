// Quantum Allosteric Scanner — frontend logic
const API = ""; // same origin (served by FastAPI)

const $ = (id) => document.getElementById(id);
let TARGETS = [];

// ── init: populate dropdowns ───────────────────────────────────────────────
async function init() {
  try {
    const [fam, tgt] = await Promise.all([
      fetch(`${API}/api/families`).then((r) => r.json()),
      fetch(`${API}/api/targets`).then((r) => r.json()),
    ]);
    fam.families.forEach((f) => addOption($("family"), f, f));
    fam.propagators.forEach((p) =>
      addOption($("propagator"), p, propagatorLabel(p))
    );
    $("propagator").value = "ctqw";

    TARGETS = tgt.targets;
    addOption($("target"), "", "— custom PDB —");
    TARGETS.forEach((t) =>
      addOption($("target"), t.name, `${t.name} · ${t.target_class}`)
    );
    $("target").addEventListener("change", onTargetChange);
    onTargetChange();
  } catch (e) {
    setStatus("Could not reach backend. Is uvicorn running?", true);
  }
}

function propagatorLabel(p) {
  return { ctqw: "CTQW (coherent quantum walk)", green: "Green (dephased quantum)", heat: "Heat (classical baseline)" }[p] || p;
}

function addOption(sel, value, label) {
  const o = document.createElement("option");
  o.value = value;
  o.textContent = label;
  sel.appendChild(o);
}

// prefill PDB/chain/source from the chosen benchmark target
function onTargetChange() {
  const name = $("target").value;
  const t = TARGETS.find((x) => x.name === name);
  // validation needs a benchmark target with a holo structure
  $("validate").disabled = !(t && t.holo);
  if (!t) return;
  $("pdb").value = t.apo || "";
  $("chains").value = t.chain || "A";
  $("source").value = (t.active_site || []).join(",");
}

// ── run scan ───────────────────────────────────────────────────────────────
$("run").addEventListener("click", runScan);

async function runScan() {
  const btn = $("run");
  btn.disabled = true;
  setStatus("Fetching structure from RCSB and running quantum propagation…");
  $("results").classList.add("hidden");

  const sourceRaw = $("source").value.trim();
  const body = {
    pdb_id: $("pdb").value.trim(),
    chains: $("chains").value.trim() || "A",
    source_residues: sourceRaw
      ? sourceRaw.split(",").map((s) => parseInt(s, 10)).filter((n) => !isNaN(n))
      : null,
    family: $("family").value,
    propagator: $("propagator").value,
    cutoff: parseFloat($("cutoff").value),
    top_k: parseInt($("topk").value, 10),
    target_name: $("target").value || null,
  };

  if (!body.pdb_id) {
    setStatus("Enter a PDB ID (or pick a benchmark target).", true);
    btn.disabled = false;
    return;
  }

  try {
    const t0 = performance.now();
    const res = await fetch(`${API}/api/scan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    const data = await res.json();
    const dt = ((performance.now() - t0) / 1000).toFixed(1);
    setStatus(
      `Done — ${data.n_residues} residues · ${data.family} · ${data.propagator} · ${dt}s`
    );
    renderHits(data);
    render3D(data);
    renderHeatmap(data);
    $("results").classList.remove("hidden");
  } catch (e) {
    setStatus(`Error: ${e.message}`, true);
  } finally {
    btn.disabled = false;
  }
}

function setStatus(msg, isError = false) {
  const s = $("status");
  s.textContent = msg;
  s.classList.toggle("error", isError);
}

// ── validate apo → holo ────────────────────────────────────────────────────
$("validate").addEventListener("click", runValidate);

async function runValidate() {
  const target = $("target").value;
  if (!target) {
    setStatus("Pick a benchmark target to validate.", true);
    return;
  }
  const btn = $("validate");
  btn.disabled = true;
  setStatus("Scanning apo structure and validating against holo ground truth…");
  $("results").classList.add("hidden");
  $("valreport").classList.add("hidden");

  const body = {
    target_name: target,
    family: $("family").value,
    propagator: $("propagator").value,
    cutoff: parseFloat($("cutoff").value),
    top_k: parseInt($("topk").value, 10),
  };

  try {
    const t0 = performance.now();
    const res = await fetch(`${API}/api/validate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    const data = await res.json();
    const dt = ((performance.now() - t0) / 1000).toFixed(1);
    setStatus(`Validated ${data.target}: apo ${data.apo} → holo ${data.validation.holo} · ${dt}s`);

    renderHits(data.scan);
    $("results").classList.remove("hidden");
    render3D(data.scan, data.validation.live_pocket || []);
    renderHeatmap(data.scan);
    renderValReport(data.validation);
    $("valreport").classList.remove("hidden");
  } catch (e) {
    setStatus(`Error: ${e.message}`, true);
  } finally {
    btn.disabled = false;
  }
}

function renderValReport(v) {
  const el = $("valbody");
  const pills = (arr, cls = "") =>
    (arr && arr.length
      ? arr.map((r) => `<span class="pill ${cls}">${r}</span>`).join("")
      : `<span class="pill">none</span>`);

  // headline metrics: prefer live-derived, fall back to frozen-pocket scan metrics
  const lm = v.live_metrics || {};
  const sm = v.scan_metrics || {};
  const auc = lm.auc_vs_live ?? sm.auc ?? "—";
  const p5 = lm["p@5_vs_live"] ?? sm["p@5"] ?? "—";

  let html = `
    <div class="vrow"><span>Ground truth (holo + drug)</span><b>${v.holo} · ${v.holo_ligand_name || v.holo_ligand || "—"}</b></div>
    ${v.holo_challenge && v.holo_challenge !== v.holo
      ? `<div class="vrow"><span>Challenge-listed holo</span><b>${v.holo_challenge}</b></div>` : ""}
    <div class="vrow"><span>Allosteric site</span><b>${v.site_name || "—"}</b></div>

    <div class="metrics-grid">
      <div class="mcard"><div class="v">${auc}</div><div class="l">AUC ${v.live_metrics ? "(vs live pocket)" : "(vs frozen)"}</div></div>
      <div class="mcard"><div class="v">${p5}</div><div class="l">Precision@5</div></div>
    </div>`;

  if (v.live_pocket) {
    html += `
      <div class="grade">Live drug-contact pocket re-derived from holo (≤${v.contact_cutoff} Å):</div>
      <div>${pills(v.live_pocket)}</div>
      <div class="vrow" style="margin-top:8px"><span>Frozen-vs-live agreement (Jaccard)</span><b>${v.frozen_vs_live_jaccard ?? "—"}</b></div>`;
  } else {
    html += `<div class="grade">No holo/ligand pocket available — discovery-only target.</div>`;
  }

  html += `
    <div class="grade">Predicted hits landing in the true pocket: <b>${v.hits_in_pocket.length}/${v.predicted_hits.length}</b></div>
    <div>${pills(v.predicted_hits.map((h) => (v.hits_in_pocket.includes(h) ? h + " ✓" : h)),
      "")}</div>`;
  if (v.top5_recovered && v.top5_recovered.length) {
    html += `<div class="grade">Recovered known top-5 residues:</div><div>${pills(v.top5_recovered, "good")}</div>`;
  }

  el.innerHTML = html;
}

// ── hit list + validation ──────────────────────────────────────────────────
function renderHits(data) {
  const ol = $("hitlist");
  ol.innerHTML = "";
  const known = new Set(data.validation?.known_top5 || []);
  data.top_hits.forEach((res, i) => {
    const li = document.createElement("li");
    const star = known.has(res) ? " ✓ (matches known site)" : "";
    li.innerHTML = `<span class="rk">#${i + 1}</span> residue ${res}${star}`;
    ol.appendChild(li);
  });

  const v = data.validation;
  const box = $("validation");
  if (v && v.metrics) {
    const m = v.metrics;
    box.innerHTML =
      `<div><b>Validation vs ${v.site_name || "known pocket"}</b></div>` +
      metric("AUC", m.auc) +
      metric("P@5", m["p@5"]) +
      metric("Enrich@5", m["enrich@5"]);
  } else if (v) {
    box.innerHTML = `<div>Discovery-only target — no validated pocket to score against.</div>`;
  } else {
    box.innerHTML = "";
  }
}

function metric(label, val) {
  return `<span class="metric">${label}: <b>${val ?? "—"}</b></span>`;
}

// ── 3D structure (3Dmol.js) ────────────────────────────────────────────────
let viewer = null;
function render3D(data, truePocket = []) {
  const el = $("viewer");
  if (!viewer) {
    viewer = $3Dmol.createViewer(el, { backgroundColor: "#05080f" });
  }
  viewer.clear();

  const pdbUrl = `https://files.rcsb.org/download/${data.pdb_id}.pdb`;
  $3Dmol.download(`pdb:${data.pdb_id}`, viewer, {}, () => {
    // base cartoon colored by quantum connectivity (norm 0..1)
    const scoreByKey = {};
    data.residues.forEach((r) => (scoreByKey[`${r.chain}_${r.resnum}`] = r));

    viewer.setStyle({}, { cartoon: { color: "#33406b" } });

    data.residues.forEach((r) => {
      const sel = { chain: r.chain, resi: r.resnum };
      if (r.is_source) {
        viewer.setStyle(sel, { cartoon: { color: "#00e6c3" } });
      } else {
        viewer.setStyle(sel, { cartoon: { color: heat(r.norm) } });
      }
    });

    // true holo-derived pocket: translucent yellow halo (ground truth)
    truePocket.forEach((res) => {
      viewer.addStyle(
        { resi: res, atom: "CA" },
        { sphere: { color: "#ffd166", radius: 2.2, opacity: 0.35 } }
      );
    });

    // highlight predicted hits as red spheres (prediction)
    data.top_hits.forEach((res) => {
      viewer.addStyle(
        { resi: res },
        { stick: { color: "#ff4d6d", radius: 0.3 } }
      );
      viewer.addStyle(
        { resi: res, atom: "CA" },
        { sphere: { color: "#ff4d6d", radius: 1.6 } }
      );
    });

    viewer.zoomTo();
    viewer.render();
  });
}

// blue → yellow → red gradient for connectivity
function heat(t) {
  t = Math.max(0, Math.min(1, t));
  const stops = [
    [43, 58, 107],
    [91, 140, 255],
    [255, 209, 102],
    [255, 77, 109],
  ];
  const x = t * (stops.length - 1);
  const i = Math.floor(x);
  const f = x - i;
  const a = stops[i];
  const b = stops[Math.min(i + 1, stops.length - 1)];
  const c = a.map((v, k) => Math.round(v + (b[k] - v) * f));
  return `rgb(${c[0]},${c[1]},${c[2]})`;
}

// ── connectivity heatmap (Plotly) ──────────────────────────────────────────
function renderHeatmap(data) {
  const z = data.connectivity_matrix;
  const ax = data.resnum_axis;
  Plotly.react(
    "heatmap",
    [{ z, x: ax, y: ax, type: "heatmap", colorscale: "Viridis", showscale: true }],
    {
      margin: { l: 50, r: 10, t: 10, b: 40 },
      paper_bgcolor: "#141b30",
      plot_bgcolor: "#141b30",
      font: { color: "#8b97b8", size: 11 },
      xaxis: { title: "residue", showgrid: false },
      yaxis: { title: "residue", showgrid: false, autorange: "reversed" },
    },
    { responsive: true, displayModeBar: false }
  );
}

init();
