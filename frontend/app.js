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
    LAST.scan = data;
    LAST.truePocket = [];
    renderHits(data);
    await loadIntel(data.pdb_id, data.chains);
    render3D();
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

    LAST.scan = data.scan;
    LAST.truePocket = data.validation.live_pocket || [];
    renderHits(data.scan);
    await loadIntel(data.scan.pdb_id, data.scan.chains);
    render3D();
    renderHeatmap(data.scan);
    renderValReport(data.validation);
    $("results").classList.remove("hidden");
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

// ── 3D structure (3Dmol.js) — state-driven, white background ────────────────
let viewer = null;
const LAST = { scan: null, intel: null, truePocket: [] };

// load structure intelligence (chains, drugs, missing residues) for a PDB
async function loadIntel(pdbId, chains) {
  try {
    const url = `${API}/api/structure?pdb_id=${encodeURIComponent(pdbId)}` +
      (chains ? `&chains=${encodeURIComponent(chains)}` : "");
    LAST.intel = await fetch(url).then((r) => (r.ok ? r.json() : null));
  } catch {
    LAST.intel = null;
  }
  renderStructInfo(LAST.intel);
}

function render3D() {
  const data = LAST.scan;
  if (!data) return;
  const el = $("viewer");
  if (!viewer) viewer = $3Dmol.createViewer(el, { backgroundColor: "#ffffff" });
  viewer.clear();

  const byChain = $("opt-cartoon-chain").checked;
  const showLig = $("opt-ligands").checked;
  const showActive = $("opt-active").checked;
  const intel = LAST.intel;

  $3Dmol.download(`pdb:${data.pdb_id}`, viewer, {}, () => {
    // base cartoon: colored by chain (biologist view) OR by quantum connectivity
    if (byChain) {
      viewer.setStyle({}, { cartoon: { colorscheme: "chain" } });
    } else {
      viewer.setStyle({}, { cartoon: { color: "#9fb0d8" } });
      data.residues.forEach((r) => {
        viewer.setStyle({ chain: r.chain, resi: r.resnum },
          { cartoon: { color: r.is_source ? "#00b89c" : heat(r.norm) } });
      });
    }

    // active site (source residues) — teal, with sticks so it's clearly visible
    if (showActive) {
      (data.source_residues || []).forEach((res) => {
        viewer.addStyle({ resi: res }, { cartoon: { color: "#00b89c" } });
        viewer.addStyle({ resi: res, atom: "CA" },
          { sphere: { color: "#00b89c", radius: 0.9 } });
      });
    }

    // true holo-derived pocket: translucent gold halo (validation ground truth)
    LAST.truePocket.forEach((res) => {
      viewer.addStyle({ resi: res, atom: "CA" },
        { sphere: { color: "#f4b400", radius: 2.2, opacity: 0.35 } });
    });

    // bound drugs / ligands — sticks + element coloring + label
    if (showLig && intel && intel.ligands) {
      intel.ligands.forEach((lig) => {
        if (lig.category === "solvent/ion") return; // skip water/ions for clarity
        const sel = { resn: lig.code, hetflag: true };
        const col = lig.is_drug ? "#b15be0" : "#5b8cff";
        viewer.addStyle(sel, { stick: { colorscheme: lig.is_drug ? "purpleCarbon" : "blueCarbon", radius: 0.18 } });
        viewer.addStyle(sel, { sphere: { scale: 0.28 } });
        viewer.addLabel(`${lig.code}${lig.is_drug ? " (drug)" : ""}`,
          { fontColor: "white", backgroundColor: col, fontSize: 11, backgroundOpacity: 0.85 },
          sel);
      });
    }

    // predicted allosteric hits — red spheres (the prediction)
    data.top_hits.forEach((res) => {
      viewer.addStyle({ resi: res }, { stick: { color: "#ff4d6d", radius: 0.3 } });
      viewer.addStyle({ resi: res, atom: "CA" },
        { sphere: { color: "#ff4d6d", radius: 1.6 } });
    });

    viewer.zoomTo();
    viewer.render();
  });
}

// re-render when a view toggle changes (no refetch needed)
["opt-cartoon-chain", "opt-ligands", "opt-active"].forEach((id) =>
  document.getElementById(id).addEventListener("change", render3D)
);

// ── structure intelligence panel ───────────────────────────────────────────
function renderStructInfo(intel) {
  const el = $("structinfo");
  if (!intel) { el.textContent = "Structure intel unavailable."; return; }
  const s = intel.summary || {};
  const drugs = intel.drugs || [];
  const ligs = intel.ligands || [];

  const card = (l, v) => `<div class="scard"><div class="l">${l}</div><div class="v">${v ?? "—"}</div></div>`;
  let html = `<div class="sgrid">
    ${card("PDB", intel.pdb_id)}
    ${card("Resolution", s.resolution ? s.resolution + " Å" : "—")}
    ${card("Method", s.method || "—")}
    ${card("Chains", (intel.chains || []).map((c) => c.chain).join(", ") || "—")}
    ${card("Drugs bound", drugs.length)}
    ${card("Missing residues", intel.n_missing)}
  </div>`;
  if (s.title) html += `<div style="margin-bottom:10px">${s.title}</div>`;

  // chains
  if (intel.chains && intel.chains.length) {
    html += `<h3>Chains</h3><table><tr><th>Chain</th><th>Residues</th><th>Range</th></tr>`;
    intel.chains.forEach((c) => {
      html += `<tr><td>${c.chain}</td><td>${c.n_residues}</td><td>${c.first}–${c.last}</td></tr>`;
    });
    html += `</table>`;
  }

  // ligands / drugs + binding sites
  if (ligs.length) {
    html += `<h3>Ligands & binding sites</h3><table><tr><th>Code</th><th>Name</th><th>Binds residues</th></tr>`;
    ligs.forEach((l) => {
      const site = (l.binding_site || []).slice(0, 12).join(", ") +
        ((l.binding_site || []).length > 12 ? " …" : "");
      html += `<tr><td>${l.code}<span class="tag ${l.category.replace("/", "\\/")}">${l.category}</span></td>` +
        `<td>${l.name || "—"}</td><td>${site || "—"}</td></tr>`;
    });
    html += `</table>`;
  }

  // missing residues
  if (intel.n_missing) {
    const list = intel.missing_residues
      .map((m) => `${m.resname}${m.resnum}${m.chain ? "/" + m.chain : ""}`)
      .join(", ");
    html += `<h3>Missing (unresolved) residues — ${intel.n_missing}</h3>` +
      `<div class="missing">${list}</div>`;
  } else {
    html += `<h3>Missing residues</h3><div>None — structure is complete.</div>`;
  }

  el.innerHTML = html;
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
