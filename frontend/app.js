// Cleveland Clinic Quantum Allosteric Scanner — Team AuraQu
// Data-foundation build: load + complete + visualize (no quantum prediction yet).
const API = ""; // same origin (served by FastAPI)

const $ = (id) => document.getElementById(id);
let TARGETS = [];
const LAST = { view: null, intel: null, shift: null };
let CURRENT_ANALYSIS = null;  // analysis object currently shown (drives charts + 3D)

// Provenance of the "Active-site residues" field: which PDB id its content belongs
// to, and whether the user typed it (manual) vs it being auto-filled from detection.
// This prevents one protein's residue numbers from carrying over to a different PDB.
let activeSitePdb = null;
let activeSiteUserEdited = false;
const curPdb = () => $("pdb").value.trim().toUpperCase();

// ── init: populate targets ─────────────────────────────────────────────────
async function init() {
  try {
    const tgt = await fetch(`${API}/api/targets`).then((r) => r.json());
    TARGETS = tgt.targets;
    addOption($("target"), "", "— custom PDB —");
    TARGETS.forEach((t) => addOption($("target"), t.name, `${t.name} · ${t.target_class}`));
    $("target").addEventListener("change", onTargetChange);
    onTargetChange();
  } catch (e) {
    setStatus("Could not reach backend. Is the server running?", true);
  }
}

function addOption(sel, value, label) {
  const o = document.createElement("option");
  o.value = value;
  o.textContent = label;
  sel.appendChild(o);
}

// prefill from the chosen benchmark target — and load it immediately
function onTargetChange(autoload = true) {
  const t = TARGETS.find((x) => x.name === $("target").value);
  if (!t) { setHoloAvailability(true); return; }
  $("pdb").value = t.apo || "";
  $("chains").value = t.chain || "A";
  $("source").value = "";  // let the backend resolve (benchmark/UniProt) + label it
  activeSiteUserEdited = false;
  activeSitePdb = null;
  // some targets (e.g. c-Myc) have NO drug-bound holo structure
  const hasHolo = !!t.holo;
  setHoloAvailability(hasHolo);
  if (!hasHolo) {
    setHoloStatus(`⚠️ ${t.name} has no holo (drug-bound) structure — apo only. Completion and apo↔holo comparison are unavailable for this target.`, true);
  } else {
    setHoloStatus("");
  }
  if (autoload) loadAndVisualize();
}

// enable/disable holo-dependent controls based on whether a holo exists
function setHoloAvailability(hasHolo) {
  $("compare").disabled = !hasHolo;
  $("complete").disabled = !hasHolo;
  if (!hasHolo) $("complete").checked = false;
}

// holo PDB for the current selection (explicit pick, else benchmark holo)
function currentHolo() {
  if ($("holo").value) return $("holo").value;
  const t = TARGETS.find((x) => x.name === $("target").value);
  return t && t.holo ? t.holo : null;
}

// the currently-loaded structure is holo if it has ≥1 bound drug/ligand
function loadedIsHolo() {
  return (((LAST.intel && LAST.intel.drugs) || []).length) >= 1;
}

// guard apo→holo comparison: a holo can't be aligned against itself (RMSD 0).
// Returns an error message to show, or null if it's OK to proceed.
function selfCompareError(apo, holo) {
  if (apo && holo && apo.toUpperCase() === holo.toUpperCase()) {
    return loadedIsHolo()
      ? "This structure is already holo (drug-bound). Enter an apo structure to compare, or pick a different holo from the list."
      : `apo and holo are the same PDB (${apo}) — enter a different apo structure to compare.`;
  }
  return null;
}

// ── find holo structures for the entered apo ───────────────────────────────
$("findholo").addEventListener("click", findHolo);

async function findHolo() {
  const apo = $("pdb").value.trim();
  if (!apo) { setHoloStatus("Enter a PDB ID first.", true); return; }
  const btn = $("findholo");
  btn.disabled = true;
  setHoloStatus("Searching RCSB for drug-bound structures of this protein…");
  try {
    const url = `${API}/api/holo-finder?apo_pdb=${encodeURIComponent(apo)}` +
      ($("target").value ? `&target_name=${encodeURIComponent($("target").value)}` : "");
    const d = await fetch(url).then((r) => r.json());
    const sel = $("holo");
    sel.innerHTML = "";
    const opts = [];
    if (d.benchmark_holo && d.benchmark_holo.holo) {
      opts.push({ v: d.benchmark_holo.holo,
        t: `${d.benchmark_holo.holo} — validated (${d.benchmark_holo.ligand_name || d.benchmark_holo.ligand || "drug"})` });
    }
    (d.candidates || []).forEach((c) => {
      if (opts.some((o) => o.v === c.pdb_id)) return;
      const tag = c.has_drug ? `drug ${c.drugs.join(",")}` : "no drug";
      opts.push({ v: c.pdb_id, t: `${c.pdb_id} — ${tag}${c.resolution ? " · " + c.resolution + "Å" : ""}` });
    });
    if (!opts.length) {
      sel.innerHTML = `<option value="">— none found —</option>`;
      setHoloAvailability(false);
      setHoloStatus(`No holo (drug-bound) structure exists for this protein (UniProt ${d.uniprot || "?"}). Comparison/completion unavailable.`, true);
    } else {
      opts.forEach((o) => addOption(sel, o.v, o.t));
      setHoloAvailability(true);
      setHoloStatus(`Found ${opts.length} structures (UniProt ${d.uniprot || "?"}).`);
    }
  } catch (e) {
    setHoloStatus(`Holo search failed: ${e.message}`, true);
  } finally {
    btn.disabled = false;
  }
}

function setHoloStatus(msg, isError = false) {
  const s = $("holostatus");
  s.textContent = msg;
  s.classList.toggle("error", isError);
}

// picking a holo from the dropdown enables comparison/completion
$("holo").addEventListener("change", () => {
  if ($("holo").value) setHoloAvailability(true);
});

// ── load & visualize ────────────────────────────────────────────────────────
$("load").addEventListener("click", loadAndVisualize);

async function loadAndVisualize() {
  const btn = $("load");
  btn.disabled = true;
  setStatus("Fetching structure from RCSB…");

  // Only treat the field as manual input if the user typed it for THIS exact PDB id;
  // otherwise ignore any leftover value and let the backend auto-detect the active
  // site (UniProt/benchmark) for the structure being loaded.
  const userTyped = activeSiteUserEdited && activeSitePdb === curPdb();
  const sourceRaw = userTyped ? $("source").value.trim() : "";
  const body = {
    pdb_id: $("pdb").value.trim(),
    chains: $("chains").value.trim() || "A",
    source_residues: sourceRaw
      ? sourceRaw.split(",").map((s) => parseInt(s, 10)).filter((n) => !isNaN(n))
      : null,
    target_name: $("target").value || null,
    complete: $("complete").checked,
    holo_pdb: $("holo").value || null,
  };
  if (!body.pdb_id) {
    setStatus("Enter a PDB ID (or pick a benchmark target).", true);
    btn.disabled = false;
    return;
  }

  try {
    const t0 = performance.now();
    const res = await fetch(`${API}/api/load`, {
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
    LAST.view = data;
    setStatus(`Loaded ${data.pdb_id} — ${data.n_residues} residues · ${dt}s`);
    showActiveSiteNote(data);
    // reset apo→holo shift state for the newly loaded structure
    LAST.shift = null;
    $("analysismode").disabled = true;
    $("analysismode").value = "loaded";
    setShiftNote("");
    $("druginter").innerHTML = "";
    renderAnalysis(data.analysis, data.active_site);
    await loadIntel(data.pdb_id, data.chains);
    render3D();
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

// show where the active site came from, and fill the field if the user left it blank
const SITE_SOURCE_LABEL = {
  benchmark: "validated benchmark", uniprot: "auto from UniProt",
  ligand: "ligand binding site (no curated active site)", manual: "your input",
  pdb_site: "PDB SITE records", none: "none found",
};
function showActiveSiteNote(data) {
  const note = $("sitenote");
  const src = data.active_site_source || "none";
  const n = (data.active_site || []).length;
  // Did the user type the current field value FOR the structure just loaded?
  const userOwnsThis = activeSiteUserEdited && activeSitePdb === data.pdb_id;
  if (src === "none" || !n) {
    note.textContent = "Active site: none found for this protein (UniProt has no annotation; no ligand pocket).";
    note.classList.add("error");
    if (!userOwnsThis) { activeSitePdb = data.pdb_id; activeSiteUserEdited = false; }
  } else {
    note.classList.remove("error");
    note.textContent = `Active site: ${SITE_SOURCE_LABEL[src] || src} — ${n} residues. ${data.active_site_detail || ""}`;
    // The field reflects this structure's detected active site, unless the user
    // deliberately typed their own list for this exact PDB id.
    if (!userOwnsThis) {
      $("source").value = (data.active_site || []).join(",");
      activeSitePdb = data.pdb_id;
      activeSiteUserEdited = false;
    }
  }
}

// Enter in the PDB or Chain field loads the structure immediately
["pdb", "chains"].forEach((id) =>
  $(id).addEventListener("keydown", (e) => {
    if (e.key === "Enter") { e.preventDefault(); loadAndVisualize(); }
  }));

// Changing the PDB id invalidates an active-site list from a previous structure:
// clear the field (and its provenance) so the new protein is auto-detected on load.
$("pdb").addEventListener("input", () => {
  if (curPdb() !== activeSitePdb) {
    $("source").value = "";
    activeSiteUserEdited = false;
    activeSitePdb = null;
    const s = $("sitenote"); s.textContent = ""; s.classList.remove("error");
  }
});

// The user typing in the field claims it as manual input for the CURRENT id only.
$("source").addEventListener("input", () => {
  activeSiteUserEdited = true;
  activeSitePdb = curPdb();
});

// ── compare apo vs holo (drug-induced movement) ─────────────────────────────
$("compare").addEventListener("click", compareApoHolo);

function setCompareStatus(msg, isError = false) {
  const s = $("comparestatus");
  s.textContent = msg;
  s.classList.toggle("error", isError);
}

async function compareApoHolo() {
  const apo = $("pdb").value.trim();
  const holo = currentHolo();
  if (!apo) { setCompareStatus("Enter the apo PDB ID first.", true); return; }
  if (!holo) { setCompareStatus("No holo found — pick one with “Find holo structures” first.", true); return; }
  const selfErr = selfCompareError(apo, holo);
  if (selfErr) { setCompareStatus(selfErr, true); return; }
  const btn = $("compare");
  btn.disabled = true;
  setCompareStatus(`Superimposing holo ${holo} onto apo ${apo}…`);
  try {
    const t = TARGETS.find((x) => x.name === $("target").value);
    const ac = ($("chains").value.trim() || "A").split(",")[0].trim();
    const hc = (t && t.chain ? t.chain : ac).split(",")[0].trim();
    const url = `${API}/api/compare?apo=${apo}&holo=${holo}&apo_chain=${ac}&holo_chain=${hc}`;
    const d = await fetch(url).then(async (r) => {
      if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || `HTTP ${r.status}`);
      return r.json();
    });
    render3DCompare(d);
    setCompareStatus(`apo ${apo} (grey) vs holo ${holo} — ${d.n_aligned} residues aligned · RMSD ${d.rmsd} Å · max Cα shift ${d.max_disp} Å`);
  } catch (e) {
    setCompareStatus(`Compare failed: ${e.message}`, true);
  } finally {
    btn.disabled = false;
  }
}

function render3DCompare(d) {
  const el = $("viewer");
  if (!viewer) viewer = $3Dmol.createViewer(el, { backgroundColor: "#ffffff" });
  viewer.clear();
  // caption: both structures overlaid
  $("viewcaption").innerHTML =
    `Showing <b class="apo">apo ${d.apo_pdb}</b> (grey) + <b class="holo">holo ${d.holo_pdb}</b> ` +
    `(colored by Cα shift), superimposed · chain <b>${d.apo_chain}</b>/<b>${d.holo_chain}</b>`;

  // apo = semi-transparent grey "ghost" reference
  const apoM = viewer.addModel(d.apo_text, "pdb");
  apoM.setStyle({}, { cartoon: { color: "#9aa0ad", opacity: 0.5 } });

  // holo = solid cartoon colored by how far each residue moved on drug binding
  const holoM = viewer.addModel(d.holo_text_aligned, "pdb");
  holoM.setStyle({}, { cartoon: { color: "#2b5ac8" } });
  const dmax = d.max_disp || 1;
  d.displacements.forEach((x) =>
    holoM.setStyle({ resi: x.resnum }, { cartoon: { color: dispColor(x.disp / dmax) } }));
  // bound drug from the holo, added on top
  holoM.setStyle({ hetflag: true }, { stick: { colorscheme: "purpleCarbon", radius: 0.25 } }, true);
  holoM.setStyle({ hetflag: true }, { sphere: { scale: 0.3 } }, true);

  viewer.zoomTo();
  viewer.render();
}

// displacement gradient: blue (no movement) → red (large shift)
function dispColor(t) {
  t = Math.max(0, Math.min(1, t));
  const a = [40, 90, 200], b = [255, 60, 50];
  const c = a.map((v, k) => Math.round(v + (b[k] - v) * t));
  return `rgb(${c[0]},${c[1]},${c[2]})`;
}

// diverging z-score colour: blue (negative) → white (0) → red (positive), ±2.5σ
function divergeColor(z) {
  const t = Math.max(-1, Math.min(1, (z || 0) / 2.5));
  const lo = [43, 90, 200], mid = [238, 242, 251], hi = [255, 77, 60];
  const [a, b, f] = t < 0 ? [mid, lo, -t] : [mid, hi, t];
  const c = a.map((v, k) => Math.round(v + (b[k] - v) * f));
  return `rgb(${c[0]},${c[1]},${c[2]})`;
}

// ── GNM site-potential analysis: enrichment + per-residue profiles ──────────
function renderAnalysis(analysis, activeSite, prefix = "", drugSite = []) {
  const enr = $("enrichment");
  const charts = $("analysischarts");
  if (!analysis) {
    CURRENT_ANALYSIS = null;
    enr.innerHTML = "";
    charts.innerHTML = "<span class='hint-line'>Site-potential analysis unavailable for this structure (too large or failed).</span>";
    return;
  }
  CURRENT_ANALYSIS = { ...analysis, active_site: activeSite || [], drug_site: drugSite || [] };
  const keys = ["V_B", "V_T", "V_R", "V_C", "V_M"];

  // enrichment cards (term − bulk z, or Δ at active site) when an active site is known
  const e = analysis.enrichment;
  if (e && Object.keys(e).length) {
    const lbl = prefix ? "Δ at active site" : "active site − bulk";
    enr.innerHTML = `<div class="hint-line">${lbl}:</div><div class="enr-grid">` + keys.map((k) => {
      const v = e[k];
      const cls = v > 0.05 ? "pos" : v < -0.05 ? "neg" : "";
      return `<div class="enr"><div class="k">${prefix}${k}</div><div class="lab">${analysis.labels[k]}</div>` +
        `<div class="val ${cls}">${v > 0 ? "+" : ""}${v.toFixed(2)}</div></div>`;
    }).join("") + `</div>`;
  } else {
    enr.innerHTML = `<span class="hint-line">No active site known — showing per-residue profiles only.</span>`;
  }

  // one profile chart per term, active-site residues marked in red
  charts.innerHTML = "";
  const siteSet = new Set(activeSite || []);
  const drugSet = new Set(drugSite || []);
  const legend = document.createElement("div");
  legend.className = "marker-legend";
  legend.innerHTML = `<span class="dot site"></span> active site` +
    (drugSet.size ? ` &nbsp; <span class="dot drug"></span> drug-binding site (holo)` : "");
  charts.appendChild(legend);
  const rmin = Math.min(...analysis.resnums);
  const rmax = Math.max(...analysis.resnums);
  ANALYSIS_CHART_DIVS.length = 0;
  keys.forEach((k, ci) => {
    const div = document.createElement("div");
    div.className = "chart";
    div.dataset.name = k;
    charts.appendChild(div);
    ANALYSIS_CHART_DIVS.push(div);
    const vals = analysis.terms[k];
    const traces = [{
      x: analysis.resnums, y: vals, type: "scatter", mode: "lines",
      line: { color: "#5b8cff", width: 1 }, fill: "tozeroy",
      fillcolor: "rgba(91,140,255,0.15)", hovertemplate: "res %{x}: %{y:.2f}<extra></extra>",
    }];
    if (siteSet.size) {
      const ax = [], ay = [];
      analysis.resnums.forEach((r, i) => { if (siteSet.has(r)) { ax.push(r); ay.push(vals[i]); } });
      traces.push({ x: ax, y: ay, type: "scatter", mode: "markers", name: "active site",
        marker: { color: "#ff4d6d", size: 5 }, hovertemplate: "active site %{x}<extra></extra>" });
    }
    if (drugSet.size) {
      const dx = [], dy = [];
      analysis.resnums.forEach((r, i) => { if (drugSet.has(r)) { dx.push(r); dy.push(vals[i]); } });
      traces.push({ x: dx, y: dy, type: "scatter", mode: "markers", name: "drug site",
        marker: { color: "#b15be0", size: 7, symbol: "diamond", line: { color: "#fff", width: 0.5 } },
        hovertemplate: "drug-binding %{x}<extra></extra>" });
    }
    const isLast = ci === keys.length - 1;
    Plotly.newPlot(div, traces, {
      margin: { l: 38, r: 10, t: 20, b: isLast ? 40 : 18 }, height: 150,
      title: { text: `${prefix}${k} · ${analysis.labels[k]}`, font: { size: 11, color: "#c7d0e6" }, x: 0.02 },
      paper_bgcolor: "#141b30", plot_bgcolor: "#141b30",
      font: { color: "#8b97b8", size: 9 },
      xaxis: {
        range: [rmin - 1, rmax + 1], showgrid: false, zeroline: false,
        nticks: 30, tickformat: "d",
        title: isLast ? { text: "residue number", font: { size: 10 } } : undefined,
      },
      yaxis: { showgrid: false, zeroline: true, zerolinecolor: "#29355c" },
      showlegend: false,
    }, { displayModeBar: false, responsive: true });
  });
}

// ── export the presented results ────────────────────────────────────────────
const ANALYSIS_CHART_DIVS = [];

function downloadFile(name, content, type) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = name; a.click();
  URL.revokeObjectURL(url);
}

function exportCSV() {
  const v = LAST.view;
  const A = CURRENT_ANALYSIS;
  if (!v || !A) { setStatus("Load a protein first.", true); return; }
  const mode = $("analysismode").value;
  const keys = ["V_B", "V_T", "V_R", "V_C", "V_M"];
  const activeSet = new Set(A.active_site || v.active_site || []);
  const drugSet = new Set((A.drug_site) || []);
  // include §5d structural change when exporting the Δ view
  const struct = (mode === "delta" && LAST.shift) ? LAST.shift.structural : null;
  const sMap = struct ? Object.fromEntries(struct.resnums.map(
    (r, i) => [r, [struct.ca_displacement[i], struct.d_coordination[i]]])) : null;
  const head = ["resnum", "is_active_site", "is_drug_site", ...keys]
    .concat(sMap ? ["ca_displacement", "d_coordination"] : []);
  const lines = [head.join(",")];
  A.resnums.forEach((rn, i) => {
    const row = [rn, activeSet.has(rn) ? 1 : 0, drugSet.has(rn) ? 1 : 0,
      ...keys.map((k) => A.terms[k][i])];
    if (sMap) row.push(...(sMap[rn] || ["", ""]));
    lines.push(row.join(","));
  });
  downloadFile(`${v.pdb_id}_site_potentials_${mode}.csv`, lines.join("\n"), "text/csv");
}

function exportJSON() {
  const v = LAST.view;
  if (!v) { setStatus("Load a protein first.", true); return; }
  const bundle = { view: v, structure_intel: LAST.intel, shift: LAST.shift };
  downloadFile(`${v.pdb_id}_results.json`, JSON.stringify(bundle, null, 2), "application/json");
}

async function exportPNG() {
  if (!ANALYSIS_CHART_DIVS.length) { setStatus("Load a protein first.", true); return; }
  for (let i = 0; i < ANALYSIS_CHART_DIVS.length; i++) {
    const div = ANALYSIS_CHART_DIVS[i];
    const uri = await Plotly.toImage(div, { format: "png", width: 1100, height: 220, scale: 2 });
    const a = document.createElement("a");
    a.href = uri; a.download = `${LAST.view.pdb_id}_${div.dataset.name || "chart" + i}.png`; a.click();
  }
}

$("exportcsv").addEventListener("click", exportCSV);
$("exportjson").addEventListener("click", exportJSON);
$("exportpng").addEventListener("click", exportPNG);

// ── apo → holo site-potential shift (notebook §5c) ──────────────────────────
$("computeshift").addEventListener("click", computeShift);
$("analysismode").addEventListener("change", applyAnalysisMode);

async function computeShift() {
  const apo = $("pdb").value.trim();
  const holo = currentHolo();
  if (!apo) { setShiftNote("Enter the apo PDB ID first.", true); return; }
  if (!holo) { setShiftNote("No holo found — pick one with “Find holo” first.", true); return; }
  const selfErr = selfCompareError(apo, holo);
  if (selfErr) { setShiftNote(selfErr, true); return; }
  const btn = $("computeshift");
  btn.disabled = true;
  setShiftNote(`Computing site potentials for holo ${holo} and the apo→holo shift…`);
  try {
    const t = TARGETS.find((x) => x.name === $("target").value);
    const ac = ($("chains").value.trim() || "A").split(",")[0].trim();
    const hc = (t && t.chain ? t.chain : ac).split(",")[0].trim();
    const url = `${API}/api/analysis-shift?apo=${apo}&holo=${holo}&apo_chain=${ac}&holo_chain=${hc}` +
      ($("target").value ? `&target_name=${encodeURIComponent($("target").value)}` : "");
    const d = await fetch(url).then(async (r) => {
      if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || `HTTP ${r.status}`);
      return r.json();
    });
    LAST.shift = d;
    $("analysismode").disabled = false;
    $("analysismode").value = "delta";
    applyAnalysisMode();
    setShiftNote(`Holo + Δ ready (${d.n_shared} shared residues). Use “Show” to switch apo / holo / Δ.`);
  } catch (e) {
    setShiftNote(`Shift failed: ${e.message}`, true);
  } finally {
    btn.disabled = false;
  }
}

function applyAnalysisMode() {
  const mode = $("analysismode").value;
  const site = (LAST.view && LAST.view.active_site) || [];
  const drug = (LAST.shift && LAST.shift.drug_site) || [];
  if (mode === "loaded" || !LAST.shift) {
    renderAnalysis(LAST.view && LAST.view.analysis, site, "", []);
    renderDrugIntersection([], []);
  } else if (mode === "holo") {
    renderAnalysis(LAST.shift.holo, site, "", drug);
    renderDrugIntersection(site, drug);
  } else {
    renderAnalysis(LAST.shift.delta, site, "Δ", drug);
    renderStructuralCharts(LAST.shift.structural, site, drug);
    renderDrugIntersection(site, drug);
  }
  render3D();  // 3D color-by + drug-site markers follow the selected analysis
}

// generic per-residue profile chart with active-site + drug-site markers
function makeProfileChart(div, o) {
  const traces = [{
    x: o.x, y: o.y, type: "scatter", mode: "lines", line: { color: o.color, width: 1 },
    fill: "tozeroy", fillcolor: o.fillColor, hovertemplate: "res %{x}: %{y:.2f}<extra></extra>",
  }];
  const mark = (set, color, symbol, size, name) => {
    if (!set || !set.size) return;
    const mx = [], my = [];
    o.x.forEach((r, i) => { if (set.has(r)) { mx.push(r); my.push(o.y[i]); } });
    traces.push({ x: mx, y: my, type: "scatter", mode: "markers", name,
      marker: { color, size, symbol, line: { color: "#fff", width: 0.5 } },
      hovertemplate: `${name} %{x}<extra></extra>` });
  };
  mark(o.siteSet, "#ff4d6d", "circle", 5, "active site");
  mark(o.drugSet, "#b15be0", "diamond", 7, "drug site");
  Plotly.newPlot(div, traces, {
    margin: { l: 44, r: 10, t: 20, b: o.isLast ? 40 : 18 }, height: 160,
    title: { text: o.title, font: { size: 11, color: "#c7d0e6" }, x: 0.02 },
    paper_bgcolor: "#141b30", plot_bgcolor: "#141b30", font: { color: "#8b97b8", size: 9 },
    xaxis: { range: [o.rmin - 1, o.rmax + 1], showgrid: false, zeroline: false, nticks: 30,
      tickformat: "d", title: o.isLast ? { text: "residue number", font: { size: 10 } } : undefined },
    yaxis: { showgrid: false, zeroline: true, zerolinecolor: "#29355c" },
    showlegend: false,
  }, { displayModeBar: false, responsive: true });
}

// §5d: apo→holo Cα displacement (Kabsch) + coordination-number change
function renderStructuralCharts(s, activeSite, drugSite) {
  if (!s) return;
  const charts = $("analysischarts");
  const siteSet = new Set(activeSite || []), drugSet = new Set(drugSite || []);
  const rmin = Math.min(...s.resnums), rmax = Math.max(...s.resnums);
  const hdr = document.createElement("div");
  hdr.className = "marker-legend";
  hdr.innerHTML = `<b style="color:var(--ink)">apo→holo structural change</b> · Cα RMSD ${s.ca_rmsd} Å · max shift ${s.max_disp} Å`;
  charts.appendChild(hdr);
  const d1 = document.createElement("div");
  d1.className = "chart"; d1.dataset.name = "ca_displacement";
  charts.appendChild(d1); ANALYSIS_CHART_DIVS.push(d1);
  makeProfileChart(d1, { title: "Cα displacement (Å) — how far each residue moves on binding",
    x: s.resnums, y: s.ca_displacement, color: "#27ae60", fillColor: "rgba(39,174,96,0.15)",
    siteSet, drugSet, isLast: false, rmin, rmax });
  const d2 = document.createElement("div");
  d2.className = "chart"; d2.dataset.name = "d_coordination";
  charts.appendChild(d2); ANALYSIS_CHART_DIVS.push(d2);
  makeProfileChart(d2, { title: "Δ coordination number (holo − apo) — contacts gained/lost",
    x: s.resnums, y: s.d_coordination, color: "#8e44ad", fillColor: "rgba(142,68,173,0.15)",
    siteSet, drugSet, isLast: true, rmin, rmax });
}

// does the drug bind AT the active site (orthosteric) or away from it (allosteric)?
function renderDrugIntersection(activeSite, drugSite) {
  const el = $("druginter");
  if (!drugSite || !drugSite.length || !activeSite || !activeSite.length) {
    el.innerHTML = "";
    return;
  }
  const aset = new Set(activeSite);
  const inter = drugSite.filter((r) => aset.has(r));
  const overlap = inter.length > 0;
  const pct = Math.round((100 * inter.length) / aset.size);
  el.innerHTML = `<div class="dcard ${overlap ? "ortho" : "allo"}">
    <div class="t">Active site ∩ drug-binding site</div>
    <div class="big">${inter.length} shared residue${inter.length === 1 ? "" : "s"}${overlap ? `: ${inter.join(", ")}` : ""}</div>
    <div class="verdict">${overlap
      ? `⚠️ The drug <b>overlaps the active site</b> (${pct}% of it) → <b>orthosteric</b> binding, at/near the catalytic site.`
      : `✓ <b>No overlap</b> with the active site → the drug binds <b>distal</b> to the catalytic site (<b>allosteric / cryptic pocket</b>).`}</div>
    <div class="sub">drug-binding residues: ${drugSite.length} · active-site residues: ${aset.size}</div>
  </div>`;
}

function setShiftNote(msg, isError = false) {
  const s = $("shiftnote");
  s.textContent = msg;
  s.classList.toggle("error", isError);
}

// ── structure intel ─────────────────────────────────────────────────────────
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

// ── 3D structure (3Dmol.js) — white background, biologist view ──────────────
let viewer = null;
// is this PDB the apo or holo of the selected target? else infer from bound drugs
function structureRole(pdbId) {
  const id = (pdbId || "").toUpperCase();
  const t = TARGETS.find((x) => x.name === $("target").value);
  if (t) {
    if (t.apo && id === t.apo.toUpperCase()) return "apo (unbound)";
    if ((t.holo && id === t.holo.toUpperCase()) ||
        (t.holo_challenge && id === t.holo_challenge.toUpperCase())) return "holo (drug-bound)";
  }
  const drugs = (LAST.intel && LAST.intel.drugs) || [];
  return drugs.length ? "holo (drug-bound)" : "apo (no drug bound)";
}

function render3D() {
  const data = LAST.view;
  if (!data) return;
  const el = $("viewer");
  if (!viewer) viewer = $3Dmol.createViewer(el, { backgroundColor: "#ffffff" });
  viewer.clear();
  // caption: which structure + chain(s) are shown
  const roleCls = structureRole(data.pdb_id).startsWith("holo") ? "holo" : "apo";
  $("viewcaption").innerHTML =
    `Showing <b class="${roleCls}">${structureRole(data.pdb_id)}</b> · ` +
    `PDB <b>${data.pdb_id}</b> · chain(s) <b>${data.chains}</b>`;

  const colorby = $("colorby").value;
  const showLig = $("opt-ligands").checked;
  const showActive = $("opt-active").checked;
  const showSurface = $("opt-surface").checked;
  const intel = LAST.intel;

  $3Dmol.download(`pdb:${data.pdb_id}`, viewer, {}, () => {
    // base cartoon
    if (colorby === "chain") {
      viewer.setStyle({}, { cartoon: { colorscheme: "chain" } });
    } else if (colorby === "flex") {
      viewer.setStyle({}, { cartoon: { color: "#9fb0d8" } });
      data.residues.forEach((r) =>
        viewer.setStyle({ chain: r.chain, resi: r.resnum },
          { cartoon: { color: flexColor(r.bnorm) } }));
    } else if (colorby.startsWith("V_") && (CURRENT_ANALYSIS || data.analysis)) {
      // color by the currently-shown GNM term (loaded / holo / Δ), diverging scale
      const A = CURRENT_ANALYSIS || data.analysis;
      const vals = A.terms[colorby] || [];
      const nums = A.resnums || [];
      viewer.setStyle({}, { cartoon: { color: "#dfe6f5" } });
      nums.forEach((rn, i) =>
        viewer.setStyle({ resi: rn }, { cartoon: { color: divergeColor(vals[i]) } }));
    } else {
      viewer.setStyle({}, { cartoon: { color: "#6f86c6" } });
    }

    // active site — teal cartoon + CA spheres
    if (showActive) {
      (data.active_site || []).forEach((res) => {
        viewer.addStyle({ resi: res }, { cartoon: { color: "#00b89c" } });
        viewer.addStyle({ resi: res, atom: "CA" }, { sphere: { color: "#00b89c", radius: 0.9 } });
      });
    }

    // drug-binding residues (from the holo) — purple, shown in holo/Δ analysis modes
    const drugSite = (CURRENT_ANALYSIS && CURRENT_ANALYSIS.drug_site) || [];
    drugSite.forEach((res) =>
      viewer.addStyle({ resi: res, atom: "CA" },
        { sphere: { color: "#b15be0", radius: 1.1 } }));

    // filled (modeled) residues are NOT in the raw PDB the viewer downloaded, so
    // draw them at their computed coordinates as orange spheres (the "added" atoms)
    const comp = data.completion;
    if (comp && comp.filled) {
      comp.filled.forEach((f) => {
        if (!f.coord) return;
        viewer.addSphere({ center: { x: f.coord[0], y: f.coord[1], z: f.coord[2] },
          radius: 1.0, color: "#ff8c2b" });
      });
    }

    // bound drugs / ligands — sticks + label
    if (showLig && intel && intel.ligands) {
      intel.ligands.forEach((lig) => {
        if (lig.category === "solvent/ion") return;
        const sel = { resn: lig.code, hetflag: true };
        const col = lig.is_drug ? "#b15be0" : "#5b8cff";
        viewer.addStyle(sel, { stick: { colorscheme: lig.is_drug ? "purpleCarbon" : "blueCarbon", radius: 0.2 } });
        viewer.addStyle(sel, { sphere: { scale: 0.3 } });
        viewer.addLabel(`${lig.code}${lig.is_drug ? " (drug)" : ""}`,
          { fontColor: "white", backgroundColor: col, fontSize: 11, backgroundOpacity: 0.85 }, sel);
      });
    }

    if (showSurface) {
      viewer.addSurface($3Dmol.SurfaceType.VDW, { opacity: 0.6, color: "#dfe6f5" });
    }

    viewer.zoomTo();
    viewer.render();
  });
}

["colorby", "opt-ligands", "opt-active", "opt-surface"].forEach((id) =>
  document.getElementById(id).addEventListener("change", render3D));

// keep the full-width viewer sized to its container on window resize
window.addEventListener("resize", () => { if (viewer) viewer.resize(); });

// blue (rigid) → red (flexible) for B-factor coloring
function flexColor(t) {
  t = Math.max(0, Math.min(1, t));
  const a = [43, 90, 200], b = [255, 77, 60];
  const c = a.map((v, k) => Math.round(v + (b[k] - v) * t));
  return `rgb(${c[0]},${c[1]},${c[2]})`;
}

// ── structure intelligence panel ───────────────────────────────────────────
function renderStructInfo(intel) {
  const el = $("structinfo");
  if (!intel) { el.textContent = "Structure intel unavailable."; return; }
  const s = intel.summary || {};
  const drugs = intel.drugs || [];
  const ligs = intel.ligands || [];
  const card = (l, v) => `<div class="scard"><div class="l">${l}</div><div class="v">${v ?? "—"}</div></div>`;
  let html = "";

  // completion banner (if missing residues were filled)
  const comp = LAST.view && LAST.view.completion;
  if (comp) {
    html += `<div class="scard" style="background:rgba(255,140,43,.12);margin-bottom:12px">
      <div class="l">Apo completion — filled from holo ${comp.holo || "?"}</div>
      <div class="v">${comp.n_filled_from_holo} from holo · ${comp.n_interpolated} interpolated · ${comp.n_unplaced} unplaced
      <span style="color:var(--muted);font-weight:400"> (of ${comp.n_missing} missing)${comp.align_rmsd != null ? ` · holo aligned onto apo, RMSD ${comp.align_rmsd} Å` : ""}</span></div>
      ${comp.filled && comp.filled.length
        ? `<details class="collapse" style="margin-top:6px"><summary>show ${comp.filled.length} filled residues</summary>
            <div style="font-size:11px" class="missing">${comp.filled.map((f) => `${f.resname}${f.resnum} <span style="opacity:.7">(${f.source})</span>`).join(", ")}</div></details>`
        : ""}
    </div>`;
  }

  html += `<div class="sgrid">
    ${card("PDB", intel.pdb_id)}
    ${card("Resolution", s.resolution ? s.resolution + " Å" : "—")}
    ${card("Method", s.method || "—")}
    ${card("Chains", (intel.chains || []).map((c) => c.chain).join(", ") || "—")}
    ${card("Drugs bound", drugs.length)}
    ${card("Missing residues", intel.n_missing)}
  </div>`;
  if (s.title) html += `<div style="margin-bottom:10px">${s.title}</div>`;

  if (intel.chains && intel.chains.length) {
    html += `<h3>Chains</h3><table><tr><th>Chain</th><th>Residues</th><th>Range</th></tr>`;
    intel.chains.forEach((c) =>
      html += `<tr><td>${c.chain}</td><td>${c.n_residues}</td><td>${c.first}–${c.last}</td></tr>`);
    html += `</table>`;
  }

  if (ligs.length) {
    html += `<h3>Ligands & binding sites</h3><table><tr><th>Code</th><th>Name</th><th>Binds residues</th></tr>`;
    ligs.forEach((l) => {
      const site = (l.binding_site || []).slice(0, 12).join(", ") +
        ((l.binding_site || []).length > 12 ? " …" : "");
      html += `<tr><td>${l.code}<span class="tag">${l.category}</span></td>` +
        `<td>${l.name || "—"}</td><td>${site || "—"}</td></tr>`;
    });
    html += `</table>`;
  }

  if (intel.n_missing) {
    const list = intel.missing_residues
      .map((m) => `${m.resname}${m.resnum}${m.chain ? "/" + m.chain : ""}`).join(", ");
    html += `<details class="collapse">
      <summary>Missing (unresolved) residues — ${intel.n_missing} <span class="hint">(click to expand)</span></summary>
      <div class="missing">${list}</div>
    </details>`;
  } else {
    html += `<h3>Missing residues</h3><div>None — structure is complete.</div>`;
  }

  el.innerHTML = html;
}

init();
