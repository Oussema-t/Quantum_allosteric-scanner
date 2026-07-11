// Cleveland Clinic Quantum Allosteric Scanner — Team AuraQu
// Data-foundation build: load + complete + visualize (no quantum prediction yet).
const API = ""; // same origin (served by FastAPI)

const $ = (id) => document.getElementById(id);
let TARGETS = [];
const LAST = { view: null, intel: null, shift: null, compare: null, mode: "single", drugSite: [] };
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
    // selecting a target only POPULATES the fields — the user sets cutoff/options
    // and clicks "Find & visualize" to load (no auto-extraction on select).
    $("target").addEventListener("change", () => onTargetChange(false));
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

// escape HTML-special characters before interpolating an externally-sourced
// string (RCSB title/ligand name/code/chain id, etc.) into innerHTML —
// defense-in-depth (TASK-0032), not an active-incident fix; RCSB is a
// curated, non-attacker-controlled source for this app's normal usage.
function escapeHtml(s) {
  if (s == null) return s;
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

// prefill the inputs from the chosen benchmark target; does NOT load (the user
// adjusts cutoff/options, then clicks "Find & visualize"). autoload kept for callers.
function onTargetChange(autoload = false) {
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
    cutoff: parseFloat($("cutoff").value) || 8.0,
    active_site_mode: $("sitemode").value,
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
    LAST.drugSite = [];
    $("analysismode").disabled = true;
    $("analysismode").value = "loaded";
    setShiftNote("");
    $("druginter").innerHTML = "";
    renderAnalysis(data.analysis, data.active_site);
    await loadIntel(data.pdb_id, data.chains);
    render3D();
    loadDrugSite();   // async: overlay where the drug binds (from the holo) onto the apo
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

// once a structure is loaded, changing ANY core parameter reloads everything
// (before the first load nothing auto-runs — the user sets options then clicks
// "Find & visualize"). cutoff re-runs the GNM; chains/complete re-fetch + re-analyze.
$("cutoff").addEventListener("change", () => { if (LAST.view) loadAndVisualize(); });
$("chains").addEventListener("change", () => { if (LAST.view) loadAndVisualize(); });
$("complete").addEventListener("change", () => { if (LAST.view) loadAndVisualize(); });

// switching active-site source (benchmark ↔ UniProt auto-detect) re-resolves it
$("sitemode").addEventListener("change", () => {
  activeSiteUserEdited = false; activeSitePdb = null;  // let the chosen source repopulate
  $("source").value = "";
  if (LAST.view) loadAndVisualize();
});

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
    // pass only the apo-chain hint; the backend resolves the DRUG-BEARING holo chain
    const ac = ($("chains").value.trim() || "A").split(",")[0].trim();
    const url = `${API}/api/compare?apo=${apo}&holo=${holo}&apo_chain=${ac}`;
    const d = await fetch(url).then(async (r) => {
      if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || `HTTP ${r.status}`);
      return r.json();
    });
    render3DCompare(d);
    setCompareStatus(`apo ${apo}/${d.apo_chain} ↔ holo ${holo}/${d.holo_chain}` +
      `${d.drug_code ? ` (drug ${d.drug_code})` : ""} — ${d.n_aligned} aligned · ` +
      `RMSD ${d.rmsd} Å · max Cα shift ${d.max_disp} Å`);
  } catch (e) {
    setCompareStatus(`Compare failed: ${e.message}`, true);
  } finally {
    btn.disabled = false;
  }
}

function render3DCompare(d) {
  LAST.mode = "compare";
  LAST.compare = d;
  const el = $("viewer");
  if (!viewer) viewer = $3Dmol.createViewer(el, { backgroundColor: "#ffffff" });
  viewer.clear();
  // caption: both structures overlaid
  $("viewcaption").innerHTML =
    `Showing <b class="apo">apo ${escapeHtml(d.apo_pdb)}</b> (grey) + <b class="holo">holo ${escapeHtml(d.holo_pdb)}</b> ` +
    `(colored by Cα shift), superimposed · apo chain <b>${escapeHtml(d.apo_chain)}</b> ↔ holo chain <b>${escapeHtml(d.holo_chain)}</b>` +
    `${d.drug_code ? ` (drug <b>${escapeHtml(d.drug_code)}</b>)` : ""}`;

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

  // descriptor-significance bar chart + Laplacian spectrum
  renderEnrichmentBar(analysis, prefix);
  renderSpectrum(analysis);

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
        marker: { symbol: "diamond-open", size: 13, color: "#b15be0", line: { color: "#b15be0", width: 2 } },
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

// download the currently visualized structure as PDB (modeled residues flagged:
// occupancy 0 / B-factor 999, listed in REMARK 470). In compare mode, export both.
function exportPDB() {
  if (LAST.mode === "compare" && LAST.compare) {
    const c = LAST.compare;
    if (c.apo_text) downloadFile(`${c.apo_pdb}_apo.pdb`, c.apo_text, "chemical/x-pdb");
    if (c.holo_text_aligned)
      downloadFile(`${c.holo_pdb}_holo_aligned.pdb`, c.holo_text_aligned, "chemical/x-pdb");
    return;
  }
  const v = LAST.view;
  if (!v || !v.pdb_text) { setStatus("Load a structure first.", true); return; }
  downloadFile(`${v.pdb_id}_visualized.pdb`, v.pdb_text, "chemical/x-pdb");
}
$("exportpdb").addEventListener("click", exportPDB);

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
    // pass only the apo-chain hint; the backend resolves the DRUG-BEARING holo chain
    const ac = ($("chains").value.trim() || "A").split(",")[0].trim();
    const cutoff = parseFloat($("cutoff").value) || 8.0;
    const url = `${API}/api/analysis-shift?apo=${apo}&holo=${holo}&apo_chain=${ac}&cutoff=${cutoff}` +
      ($("target").value ? `&target_name=${encodeURIComponent($("target").value)}` : "");
    const d = await fetch(url).then(async (r) => {
      if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || `HTTP ${r.status}`);
      return r.json();
    });
    LAST.shift = d;
    $("analysismode").disabled = false;
    $("analysismode").value = "delta";
    applyAnalysisMode();
    const cu = d.chains_used || {};
    setShiftNote(`Holo + Δ ready — apo chain ${cu.apo_chain} ↔ holo chain ${cu.holo_chain}` +
      `${cu.drug_code ? ` (drug ${cu.drug_code})` : ""}, ${d.n_shared} shared residues. ` +
      `Use “Show” to switch apo / holo / Δ.`);
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
    renderAnalysis(LAST.view && LAST.view.analysis, site, "", LAST.drugSite || []);
    renderDrugIntersection(site, LAST.drugSite || []);
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

// descriptor enrichment bar chart, coloured by permutation significance
function renderEnrichmentBar(analysis, prefix) {
  const div = $("enrichbar");
  const e = analysis.enrichment;
  if (!e || !Object.keys(e).length) { Plotly.purge(div); div.style.display = "none"; return; }
  div.style.display = "";
  const keys = ["V_B", "V_T", "V_R", "V_C", "V_M"];
  const sig = analysis.enrichment_sig || {};
  const y = keys.map((k) => e[k]);
  const colors = keys.map((k) => (sig[k] && sig[k].sig) ? "#c0392b" : "#7f8db0");
  const cd = keys.map((k) => (sig[k] ? sig[k].p : null));
  const lbl = prefix ? "Δ at active site" : "active site − bulk";
  Plotly.newPlot(div, [{
    x: keys.map((k) => `${prefix}${k}`), y, type: "bar",
    marker: { color: colors }, customdata: cd,
    hovertemplate: "%{x}: %{y}<br>p=%{customdata}<extra></extra>",
  }], {
    title: { text: `Descriptor signal (${lbl}) — red = permutation-significant (p<0.05)`, font: { size: 11, color: "#c7d0e6" }, x: 0.02 },
    margin: { l: 42, r: 10, t: 26, b: 30 }, height: 240,
    paper_bgcolor: "#141b30", plot_bgcolor: "#141b30", font: { color: "#8b97b8", size: 10 },
    xaxis: { showgrid: false },
    yaxis: { title: lbl + " (z)", showgrid: false, zeroline: true, zerolinecolor: "#29355c" },
  }, { displayModeBar: false, responsive: true });
}

// histogram of the contact-Laplacian eigenvalues (network spectrum)
function renderSpectrum(analysis) {
  const div = $("lspectrum");
  if (!analysis.l_eigs || !analysis.l_eigs.length) { Plotly.purge(div); div.style.display = "none"; return; }
  div.style.display = "";
  Plotly.newPlot(div, [{
    x: analysis.l_eigs, type: "histogram", nbinsx: 40, marker: { color: "#2c3e50" },
    hovertemplate: "λ≈%{x}: %{y}<extra></extra>",
  }], {
    title: { text: "Contact-Laplacian spectrum (eigenvalues λ)", font: { size: 11, color: "#c7d0e6" }, x: 0.02 },
    margin: { l: 42, r: 10, t: 26, b: 30 }, height: 220,
    paper_bgcolor: "#141b30", plot_bgcolor: "#141b30", font: { color: "#8b97b8", size: 10 },
    xaxis: { title: "λ", showgrid: false }, yaxis: { title: "count", showgrid: false },
  }, { displayModeBar: false, responsive: true });
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
    const open = symbol.indexOf("open") >= 0;  // hollow markers: outline in `color`
    traces.push({ x: mx, y: my, type: "scatter", mode: "markers", name,
      marker: { color, size, symbol, line: { color: open ? color : "#fff", width: open ? 2 : 0.5 } },
      hovertemplate: `${name} %{x}<extra></extra>` });
  };
  mark(o.siteSet, "#ff4d6d", "circle", 5, "active site");
  mark(o.drugSet, "#b15be0", "diamond-open", 13, "drug site");  // hollow so an active-site dot shows through
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

// fetch where the drug binds (from the known holo) and overlay it on the apo view
async function loadDrugSite() {
  const holo = currentHolo();
  if (!holo || !LAST.view) return;
  try {
    const d = await fetch(`${API}/api/drug-site?holo=${encodeURIComponent(holo)}`)
      .then((r) => (r.ok ? r.json() : null));
    if (!d || !d.drug_site || !d.drug_site.length) return;
    LAST.drugSite = d.drug_site;
    // refresh the loaded/apo view so the drug-binding residues appear (holo/Δ modes
    // already carry their own drug site from the shift computation)
    if (!LAST.shift || $("analysismode").value === "loaded") {
      renderAnalysis(LAST.view.analysis, LAST.view.active_site, "", LAST.drugSite);
      renderDrugIntersection(LAST.view.active_site, LAST.drugSite);
      render3D();
    }
  } catch { /* drug overlay is best-effort */ }
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
  LAST.mode = "single";
  const el = $("viewer");
  if (!viewer) viewer = $3Dmol.createViewer(el, { backgroundColor: "#ffffff" });
  viewer.clear();
  // caption: which structure + chain(s) are shown
  const roleCls = structureRole(data.pdb_id).startsWith("holo") ? "holo" : "apo";
  $("viewcaption").innerHTML =
    `Showing <b class="${roleCls}">${structureRole(data.pdb_id)}</b> · ` +
    `PDB <b>${escapeHtml(data.pdb_id)}</b> · chain(s) <b>${escapeHtml(data.chains)}</b>`;

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

    // bound drugs / ligands — sticks + a label per INSTANCE, anchored to that copy's
    // centroid (explicit world position → stays put on zoom; handles duplicate codes)
    if (showLig && intel && intel.ligands) {
      const model = viewer.getModel();
      intel.ligands.forEach((lig) => {
        if (lig.category === "solvent/ion") return;
        const sel = { resn: lig.code, chain: lig.chain, resi: lig.resnum, hetflag: true };
        const col = lig.is_drug ? "#b15be0" : "#5b8cff";
        viewer.addStyle(sel, { stick: { colorscheme: lig.is_drug ? "purpleCarbon" : "blueCarbon", radius: 0.2 } });
        viewer.addStyle(sel, { sphere: { scale: 0.3 } });
        const atoms = (model && model.selectedAtoms(sel)) || [];
        if (!atoms.length) return;
        let cx = 0, cy = 0, cz = 0;
        atoms.forEach((a) => { cx += a.x; cy += a.y; cz += a.z; });
        cx /= atoms.length; cy /= atoms.length; cz /= atoms.length;
        viewer.addLabel(`${lig.code}${lig.is_drug ? " (drug)" : ""}`, {
          fontColor: "white", backgroundColor: col, fontSize: 11, backgroundOpacity: 0.85,
          inFront: true, position: { x: cx, y: cy, z: cz },
        });
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
      <div class="l">Apo completion — filled from holo ${escapeHtml(comp.holo) || "?"}</div>
      <div class="v">${comp.n_filled_from_holo} from holo · ${comp.n_interpolated} interpolated · ${comp.n_unplaced} unplaced
      <span style="color:var(--muted);font-weight:400"> (of ${comp.n_missing} missing)${comp.align_rmsd != null ? ` · holo aligned onto apo, RMSD ${comp.align_rmsd} Å` : ""}</span></div>
      ${comp.filled && comp.filled.length
        ? `<details class="collapse" style="margin-top:6px"><summary>show ${comp.filled.length} filled residues</summary>
            <div style="font-size:11px" class="missing">${comp.filled.map((f) => `${escapeHtml(f.resname)}${f.resnum} <span style="opacity:.7">(${f.source})</span>`).join(", ")}</div></details>`
        : ""}
    </div>`;
  }

  html += `<div class="sgrid">
    ${card("PDB", escapeHtml(intel.pdb_id))}
    ${card("Resolution", s.resolution ? s.resolution + " Å" : "—")}
    ${card("Method", escapeHtml(s.method) || "—")}
    ${card("Chains", (intel.chains || []).map((c) => escapeHtml(c.chain)).join(", ") || "—")}
    ${card("Drugs bound", drugs.length)}
    ${card("Missing residues", intel.n_missing)}
  </div>`;
  if (s.title) html += `<div style="margin-bottom:10px">${escapeHtml(s.title)}</div>`;

  if (intel.chains && intel.chains.length) {
    html += `<h3>Chains</h3><table><tr><th>Chain</th><th>Residues</th><th>Range</th></tr>`;
    intel.chains.forEach((c) =>
      html += `<tr><td>${escapeHtml(c.chain)}</td><td>${c.n_residues}</td><td>${c.first}–${c.last}</td></tr>`);
    html += `</table>`;
  }

  if (ligs.length) {
    html += `<h3>Ligands & binding sites</h3><table><tr><th>Code</th><th>Name</th><th>Binds residues</th></tr>`;
    ligs.forEach((l) => {
      const site = (l.binding_site || []).slice(0, 12).join(", ") +
        ((l.binding_site || []).length > 12 ? " …" : "");
      html += `<tr><td>${escapeHtml(l.code)}<span class="tag">${escapeHtml(l.category)}</span></td>` +
        `<td>${escapeHtml(l.name) || "—"}</td><td>${site || "—"}</td></tr>`;
    });
    html += `</table>`;
  }

  if (intel.n_missing) {
    const list = intel.missing_residues
      .map((m) => `${escapeHtml(m.resname)}${m.resnum}${m.chain ? "/" + escapeHtml(m.chain) : ""}`).join(", ");
    html += `<details class="collapse">
      <summary>Missing (unresolved) residues — ${intel.n_missing} <span class="hint">(click to expand)</span></summary>
      <div class="missing">${list}</div>
    </details>`;
  } else {
    html += `<h3>Missing residues</h3><div>None — structure is complete.</div>`;
  }

  el.innerHTML = html;
}

// ── apo→holo connectivity change (DDM · rewiring · ΔDCC + morph) ────────────
$("connbtn").addEventListener("click", computeConnectivityChange);

const DIVERGE = [[0, "#2166ac"], [0.5, "#f7f7f7"], [1, "#b2182b"]];

async function computeConnectivityChange() {
  const apo = $("pdb").value.trim();
  const holo = currentHolo();
  if (!apo) { setConnStatus("Enter the apo PDB ID first.", true); return; }
  if (!holo) { setConnStatus("No holo found — pick one with “Find holo” first.", true); return; }
  const selfErr = selfCompareError(apo, holo);
  if (selfErr) { setConnStatus(selfErr, true); return; }
  const btn = $("connbtn"); btn.disabled = true;
  setConnStatus(`Computing apo→holo connectivity change (${apo} → ${holo})…`);
  try {
    const ac = ($("chains").value.trim() || "A").split(",")[0].trim();
    const cutoff = parseFloat($("cutoff").value) || 8.0;
    const url = `${API}/api/connectivity-change?apo=${apo}&holo=${holo}&apo_chain=${ac}&cutoff=${cutoff}` +
      ($("target").value ? `&target_name=${encodeURIComponent($("target").value)}` : "");
    const d = await fetch(url).then(async (r) => {
      if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || `HTTP ${r.status}`);
      return r.json();
    });
    LAST.conn = d;
    LAST.frames = null;                      // real frames are stale until re-fetched
    renderConnSummary(d);
    renderSeedReadiness(d.seed_readiness);   // §5h/§5i — before the 3D graph
    ["connX", "connY"].forEach((id) => ($(id).value = "all"));
    $("connXint").value = ""; $("connYint").value = "";
    $("connfilter").classList.remove("hidden");
    applyConnRegion();   // renders heatmaps + morph + 3D graph (all residues initially)
  } catch (e) {
    setConnStatus(`Failed: ${e.message}`, true);
  } finally {
    btn.disabled = false;
  }
}

function setConnStatus(msg, isError = false) {
  const s = $("connstatus"); s.textContent = msg; s.classList.toggle("error", isError);
}

function renderConnSummary(d) {
  const s = d.summary;
  const card = (l, v) => `<span class="scard"><span class="v">${v}</span> <span class="l">${l}</span></span>`;
  $("connsummary").innerHTML =
    card("max |ΔdistÅ|", s.ddm_max) + card("contacts formed", "+" + s.contacts_formed) +
    card("contacts broken", "−" + s.contacts_broken) + card("mean |ΔDCC|", s.mean_abs_ddcc) +
    `<div style="margin-top:8px">Most-reorganized residues (DDM): <b style="color:var(--ink)">${s.most_reorganized.join(", ")}</b></div>`;
}

// §5h/§5i — quantum-seed readiness card (apo vs holo) shown before the 3D graph
function seedVerdictBadge(v) {
  const cls = { SAFE: "sb-safe", PARTIAL: "sb-partial", RISKY: "sb-risky" }[v] || "sb-neutral";
  return `<span class="seed-badge ${cls}">${v}</span>`;
}

// raw apo→holo shift table for a residue set, with 2σ-significance markers
function seedShiftTable(title, shift) {
  if (!shift) return "";
  const dcol = (x) => (x > 0 ? "#5fb89b" : x < 0 ? "#c77b73" : "#8b97b8");
  const sigtag = (s) => s
    ? `<span style="color:var(--accent)">✓ &gt;2σ</span>`
    : `<span style="color:#8b97b8">ns</span>`;
  const labels = { msf: "flexibility (MSF, ↓ = more rigid)", coupling: "dynamic coupling (|nDCC|)", slow: "slow-mode participation" };
  const rows = ["msf", "coupling", "slow"].map((k) => {
    const dv = shift.delta[k];
    return `<tr><td style="text-align:left">${labels[k]}</td><td>${shift.apo[k].toFixed(3)}</td>` +
      `<td>${shift.holo[k].toFixed(3)}</td><td style="color:${dcol(dv)}">${(dv >= 0 ? "+" : "") + dv.toFixed(3)}</td>` +
      `<td>${sigtag(shift.sig[k])}</td></tr>`;
  }).join("");
  return `<div class="status" style="margin-top:8px">${title}</div>
    <table class="seed-table"><thead><tr><th style="text-align:left">descriptor (raw)</th><th>apo</th><th>holo</th><th>Δ</th><th>sig.</th></tr></thead><tbody>${rows}</tbody></table>`;
}

function renderSeedReadiness(sr) {
  const wrap = $("seedwrap");
  if (!sr || !sr.apo || !sr.holo) { wrap.classList.add("hidden"); return; }
  wrap.classList.remove("hidden");
  const a = sr.apo, h = sr.holo;
  const mechCol = { ACTIVATION: "#5fb89b", DEACTIVATION: "#c77b73", AMBIGUOUS: "#c2a04e" }[sr.mechanism] || "#8b97b8";

  const sep = (sr.drug_active_sep != null) ? `${sr.drug_active_sep} Å` : "n/a";
  const topoLine = (sr.topology && sr.topology !== "unknown")
    ? `<div class="status" style="margin:2px 0 8px">Drug binding (auto from geometry): <b style="color:var(--ink)">${sr.topology}</b> · ${sr.n_pocket} pocket residues · min drug–active-site separation ${sep}</div>`
    : `<div class="status" style="margin:2px 0 8px">Drug pocket not resolved — mechanism read from the active site only.</div>`;

  const reachLine = `<div class="status" style="margin-top:6px">Distal-reach enrichment shift (size-invariant): <b style="color:${sr.reach_shift > 0 ? "#5fb89b" : sr.reach_shift < 0 ? "#c77b73" : "#8b97b8"}">${(sr.reach_shift >= 0 ? "+" : "") + sr.reach_shift}×</b></div>`;

  const prRows = a.per_residue.map((r) =>
    `<tr style="color:${r.status === "weak" ? "#c77b73" : "var(--ink)"}">` +
    `<td>${r.resnum}</td><td>${r.degree}</td><td>${r.coupling.toFixed(2)}</td>` +
    `<td>${r.rigidity.toFixed(2)}</td><td>${r.modeled ? "yes" : "—"}</td>` +
    `<td style="text-align:left">${r.status === "weak" ? r.reasons : "good"}</td></tr>`).join("");
  const recommend = (a.recommend_seed.length && a.n_good < a.n_total)
    ? `<div class="status" style="margin-top:6px">Recommended seed (reliable subset): <b style="color:var(--ink)">${a.recommend_seed.join(", ")}</b></div>` : "";

  $("seedbody").innerHTML = `
    <div style="display:flex;gap:24px;flex-wrap:wrap;margin:6px 0 6px">
      <div>apo seed: ${seedVerdictBadge(a.verdict)} <span class="status">${a.detail}</span></div>
      <div>holo seed: ${seedVerdictBadge(h.verdict)} <span class="status">${h.detail}</span></div>
    </div>
    ${topoLine}
    <div style="margin:8px 0;padding:8px 10px;border-left:3px solid ${mechCol};background:#141b30">
      <b style="color:${mechCol}">Drug mechanism (hypothesis): ${sr.mechanism}</b>
      <span class="status"> — ${sr.mechanism_detail}</span>
    </div>
    ${seedShiftTable("apo→holo shift at the active site (readout):", sr.active_shift)}
    ${seedShiftTable("apo→holo shift at the drug-binding pocket:", sr.pocket_shift)}
    ${reachLine}
    ${recommend}
    <details style="margin-top:8px"><summary class="status" style="cursor:pointer">Per-residue apo seed audit (${a.n_good}/${a.n_total} reliable)</summary>
      <table class="seed-table"><thead><tr><th>res</th><th>degree</th><th>coupling</th><th>rigidity</th><th>modeled</th><th style="text-align:left">flag</th></tr></thead><tbody>${prRows}</tbody></table>
    </details>`;
}

// thin grid lines marking landmark residues on a (possibly non-square) matrix:
// teal = active site, purple = drug-binding. Vertical lines for X (cols), horizontal for Y (rows).
function landmarkShapes(xax, yax, activeSet, drugSet) {
  const xlo = xax[0], xhi = xax[xax.length - 1], ylo = yax[0], yhi = yax[yax.length - 1];
  const vline = (v, color) => ({ type: "line", x0: v, x1: v, y0: ylo, y1: yhi, line: { color, width: 0.5 }, opacity: 0.6 });
  const hline = (v, color) => ({ type: "line", y0: v, y1: v, x0: xlo, x1: xhi, line: { color, width: 0.5 }, opacity: 0.6 });
  const shapes = [];
  xax.forEach((v) => { if (drugSet.has(v)) shapes.push(vline(v, "#b15be0")); if (activeSet.has(v)) shapes.push(vline(v, "#00e6c3")); });
  yax.forEach((v) => { if (drugSet.has(v)) shapes.push(hline(v, "#b15be0")); if (activeSet.has(v)) shapes.push(hline(v, "#00e6c3")); });
  return shapes;
}

function connHeatmap(div, z, title, xax, yax, activeSet, drugSet, zmid, zmin, zmax) {
  const shapes = landmarkShapes(xax, yax, activeSet, drugSet);
  Plotly.newPlot(div, [{
    z, x: xax, y: yax, type: "heatmap", colorscale: DIVERGE,
    zmid: zmid, zmin: zmin, zmax: zmax, showscale: true,
    hovertemplate: "row %{y} · col %{x}: %{z}<extra></extra>",
  }], {
    title: { text: title, font: { size: 11, color: "#c7d0e6" }, x: 0.02 },
    margin: { l: 40, r: 10, t: 26, b: 36 }, paper_bgcolor: "#141b30", plot_bgcolor: "#141b30",
    font: { color: "#8b97b8", size: 9 }, shapes,
    xaxis: { title: "residue (cols)", showgrid: false }, yaxis: { title: "residue (rows)", showgrid: false, autorange: "reversed" },
  }, { displayModeBar: false, responsive: true });
}

// render the three matrices restricted to a Y (rows) × X (cols) residue sub-block
function renderConnHeatmaps(d, rowIdx, colIdx) {
  const xax = colIdx.map((i) => d.resnums[i]);
  const yax = rowIdx.map((i) => d.resnums[i]);
  const slice = (M) => rowIdx.map((i) => colIdx.map((j) => M[i][j]));
  const ddm = slice(d.ddm), rewire = slice(d.rewire), ddcc = slice(d.ddcc);
  const activeSet = new Set(d.active_site || []);
  const drugSet = new Set(d.drug_site || []);
  const ddmLim = matAbsPct(ddm, 99);
  const ddccLim = matAbsPct(ddcc, 99);
  connHeatmap($("ddmplot"), ddm, "DDM — distance change (red = apart, blue = closer)", xax, yax, activeSet, drugSet, 0, -ddmLim, ddmLim);
  connHeatmap($("rewireplot"), rewire, "Contact rewiring (+1 formed / −1 broken)", xax, yax, activeSet, drugSet, 0, -1, 1);
  connHeatmap($("ddccplot"), ddcc, "ΔDCC — dynamic coupling change (holo − apo)", xax, yax, activeSet, drugSet, 0, -ddccLim, ddccLim);
}

// ── residue-region selection (filter all connectivity views) ────────────────
function parseRanges(text) {
  return (text || "").split(",").map((s) => s.trim()).filter(Boolean).map((s) => {
    const p = s.split("-").map((x) => parseInt(x, 10));
    if (p.length === 2 && !isNaN(p[0]) && !isNaN(p[1])) return [Math.min(p[0], p[1]), Math.max(p[0], p[1])];
    if (p.length === 1 && !isNaN(p[0])) return [p[0], p[0]];
    return null;
  }).filter(Boolean);
}

function resolveRegion(sel, intervalText, d) {
  const ax = d.resnums;
  if (sel === "active") { const s = new Set(d.active_site || []); return ax.map((r, i) => (s.has(r) ? i : -1)).filter((i) => i >= 0); }
  if (sel === "drug") { const s = new Set(d.drug_site || []); return ax.map((r, i) => (s.has(r) ? i : -1)).filter((i) => i >= 0); }
  if (sel === "interval") { const R = parseRanges(intervalText); return ax.map((r, i) => (R.some(([a, b]) => r >= a && r <= b) ? i : -1)).filter((i) => i >= 0); }
  return ax.map((_, i) => i);
}

function subsetConn(d, idx) {
  return {
    apo_coords: idx.map((i) => d.apo_coords[i]), holo_coords: idx.map((i) => d.holo_coords[i]),
    resnums: idx.map((i) => d.resnums[i]), cutoff: d.cutoff, r0: d.r0,
    active_site: d.active_site, drug_site: d.drug_site,
  };
}

function graphMotionMode() { return $("graphmode") ? $("graphmode").value : "linear"; }

// restrict a real-frames payload to residues in `regionSet` (by residue NUMBER, since the
// frames live on a different shared-residue set than LAST.conn). null if <2 residues remain.
function subsetFrames(fp, regionSet) {
  const keep = [];
  for (let i = 0; i < fp.resnums.length; i++) if (regionSet.has(fp.resnums[i])) keep.push(i);
  if (keep.length < 2) return null;
  return {
    resnums: keep.map((i) => fp.resnums[i]), cutoff: fp.cutoff, frame_labels: fp.frame_labels,
    frames: fp.frames.map((fr) => keep.map((i) => fr[i])),
    apo_coords: keep.map((i) => fp.frames[0][i]),
    holo_coords: keep.map((i) => fp.frames[fp.frames.length - 1][i]),
  };
}

function applyConnRegion() {
  const d = LAST.conn;
  if (!d) return;
  let rowIdx = resolveRegion($("connY").value, $("connYint").value, d);
  let colIdx = resolveRegion($("connX").value, $("connXint").value, d);
  if (!rowIdx.length) rowIdx = d.resnums.map((_, i) => i);
  if (!colIdx.length) colIdx = d.resnums.map((_, i) => i);
  renderConnHeatmaps(d, rowIdx, colIdx);
  // morph + 3D graph use the union of the selected residues (a single node set)
  const uni = Array.from(new Set([...rowIdx, ...colIdx])).sort((a, b) => a - b);
  const sub = subsetConn(d, uni);
  setupMorph(sub);
  const activeSet = new Set(d.active_site || []), drugSet = new Set(d.drug_site || []);
  // 3D graph: in real-structures mode, restrict the real frames to this region too;
  // otherwise the straight-line graph on the region subset.
  const realFrames = (graphMotionMode() === "real" && LAST.frames)
    ? subsetFrames(LAST.frames, new Set(uni.map((i) => d.resnums[i]))) : null;
  setupGraphMorph(realFrames || sub, activeSet, drugSet);
  const full = d.resnums.length;
  const note = (rowIdx.length < full || colIdx.length < full)
    ? `showing ${rowIdx.length}×${colIdx.length} residues (morph/graph: ${uni.length})`
    : "showing all residues";
  setConnStatus(`${d.n_shared} shared residues · ${note}.`);
}

$("connapply").addEventListener("click", applyConnRegion);
$("connreset").addEventListener("click", () => {
  ["connX", "connY"].forEach((id) => ($(id).value = "all"));
  $("connXint").value = ""; $("connYint").value = ""; applyConnRegion();
});
["connX", "connY"].forEach((id) => $(id).addEventListener("change", applyConnRegion));
["connXint", "connYint"].forEach((id) => $(id).addEventListener("keydown", (e) => {
  if (e.key === "Enter") { e.preventDefault(); applyConnRegion(); }
}));

// ── animated 3D protein contact graph (apo → holo) ─────────────────────────
// nodes morph from apo to holo 3D positions; edges form/break live (kept/formed/broken).
// Uses the real Cα coordinates (no projection); drag to rotate, scroll to zoom.
let GRAPH = { data: null, t: 0, dir: 1, timer: null };
const _gdist = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);

function setupGraphMorph(d, activeSet, drugSet) {
  $("graphwrap").classList.remove("hidden");
  const ax = d.resnums, cut = d.cutoff;
  // keyframes: real frames [apo, …intermediates, holo] if provided, else the 2-frame straight line
  const frames = (d.frames && d.frames.length >= 2) ? d.frames : [d.apo_coords, d.holo_coords];
  const apo3 = frames[0], holo3 = frames[frames.length - 1];  // endpoints decide formed/broken
  const edges = [];                                   // pairs that are a contact in apo OR holo
  for (let i = 0; i < ax.length; i++) for (let j = i + 1; j < ax.length; j++) {
    const ea = _gdist(apo3[i], apo3[j]) < cut, eh = _gdist(holo3[i], holo3[j]) < cut;
    if (ea || eh) edges.push([i, j, ea && eh ? 0 : eh ? 1 : 2]);  // 0 kept · 1 formed · 2 broken
  }
  const ncolor = ax.map((r) => (activeSet.has(r) && drugSet.has(r)) ? "#ffd166"
    : activeSet.has(r) ? "#00e6c3" : drugSet.has(r) ? "#b15be0" : "#7f8db0");
  const nsize = ax.map((r) => (activeSet.has(r) || drugSet.has(r)) ? 6 : 3);
  const ntext = ax.map((r) => `res ${r}${activeSet.has(r) ? " · active" : ""}${drugSet.has(r) ? " · drug" : ""}`);
  GRAPH.data = { frames, apo3, holo3, edges, cut, ncolor, nsize, ntext };
  GRAPH.labels = d.frame_labels || ["apo", "holo"];
  GRAPH.t = 0; GRAPH.dir = 1;
  const f = graphFrameData(0);
  const eTrace = (e, color, w, op) => ({ type: "scatter3d", mode: "lines", x: e.x, y: e.y, z: e.z,
    line: { color, width: w }, opacity: op, hoverinfo: "skip" });
  Plotly.newPlot("protgraph", [
    eTrace(f.kept, "#8a93b8", 1.5, 0.2),
    eTrace(f.broken, "#d62728", 3.5, 0.9),
    eTrace(f.formed, "#2ca02c", 3.5, 0.9),
    { type: "scatter3d", mode: "markers", x: f.nx, y: f.ny, z: f.nz,
      marker: { color: ncolor, size: nsize, line: { color: "#0b1020", width: 0.5 } },
      text: ntext, hovertemplate: "%{text}<extra></extra>" },
  ], {
    margin: { l: 0, r: 0, t: 0, b: 0 }, paper_bgcolor: "#141b30", showlegend: false,
    scene: {
      xaxis: { visible: false }, yaxis: { visible: false }, zaxis: { visible: false },
      aspectmode: "data", bgcolor: "#141b30",
    },
  }, { displayModeBar: false, responsive: true });
  startGraph();
}

function graphFrameData(t) {
  const g = GRAPH.data, F = g.frames, K = F.length;
  // map global t∈[0,1] across the K−1 segments, then interpolate within the segment
  const seg = Math.min(Math.floor(t * (K - 1)), K - 2);
  const u = t * (K - 1) - seg;                        // local 0→1 within this segment
  const A = F[seg], B = F[seg + 1];
  const P = A.map((p, i) => [
    (1 - u) * p[0] + u * B[i][0], (1 - u) * p[1] + u * B[i][1], (1 - u) * p[2] + u * B[i][2]]);
  const nx = [], ny = [], nz = [];
  for (const p of P) { nx.push(p[0]); ny.push(p[1]); nz.push(p[2]); }
  const kept = { x: [], y: [], z: [] }, formed = { x: [], y: [], z: [] }, broken = { x: [], y: [], z: [] };
  for (const [i, j, cls] of g.edges) {
    const dd = _gdist(P[i], P[j]);
    if (dd < g.cut && dd > 1e-8) {              // edge present at this frame
      const b = cls === 0 ? kept : cls === 1 ? formed : broken;
      b.x.push(P[i][0], P[j][0], null); b.y.push(P[i][1], P[j][1], null); b.z.push(P[i][2], P[j][2], null);
    }
  }
  return { kept, formed, broken, nx, ny, nz };
}

function graphFrame(t) {
  const f = graphFrameData(t);
  // restyle preserves the camera, so the user can keep rotating while it animates
  Plotly.restyle("protgraph",
    { x: [f.kept.x, f.broken.x, f.formed.x, f.nx], y: [f.kept.y, f.broken.y, f.formed.y, f.ny], z: [f.kept.z, f.broken.z, f.formed.z, f.nz] },
    [0, 1, 2, 3]);
  const L = GRAPH.labels || ["apo", "holo"], K = L.length;
  const near = Math.round(t * (K - 1));               // nearest keyframe label
  const tag = (t < 0.01) ? L[0] : (t > 0.99) ? L[K - 1]
    : (Math.abs(t * (K - 1) - near) < 0.04 ? `@ ${L[near]}` : (GRAPH.dir > 0 ? "→ holo" : "→ apo"));
  $("grapht").textContent = `t = ${t.toFixed(2)} (${tag})`;
  $("graphslider").value = t;
}

function startGraph() {
  if (GRAPH.timer) return;
  GRAPH.timer = setInterval(() => {
    GRAPH.t += 0.04 * GRAPH.dir;
    if (GRAPH.t >= 1) { GRAPH.t = 1; GRAPH.dir = -1; }
    else if (GRAPH.t <= 0) { GRAPH.t = 0; GRAPH.dir = 1; }
    graphFrame(GRAPH.t);
  }, 150);
  $("graphplay").textContent = "⏸ Pause";
}
function stopGraph() {
  if (GRAPH.timer) { clearInterval(GRAPH.timer); GRAPH.timer = null; }
  $("graphplay").textContent = "▶ Play";
}
$("graphplay").addEventListener("click", () => { GRAPH.timer ? stopGraph() : startGraph(); });
$("graphslider").addEventListener("input", (e) => { stopGraph(); GRAPH.t = parseFloat(e.target.value); graphFrame(GRAPH.t); });

// switch the 3D-graph motion: straight-line (current region) vs real intermediate frames
async function applyGraphMotion() {
  const st = $("graphmotionstatus");
  if (!LAST.conn) { st.textContent = "Run “Compute connectivity change” first."; return; }
  if ($("graphmode").value === "linear") {
    st.textContent = "Straight-line apo → holo (linear interpolation).";
    applyConnRegion();                                 // rebuild the graph from the current region
    return;
  }
  const apo = $("pdb").value.trim(), holo = currentHolo();
  const nFrames = parseInt($("graphnframes").value, 10) || 4;
  const ac = ($("chains").value.trim() || "A").split(",")[0].trim();
  // use the SAME cutoff the connectivity graph was built with, so both modes match exactly
  const cutoff = (LAST.conn && LAST.conn.cutoff) || parseFloat($("cutoff").value) || 8.0;
  const btn = $("graphapply"); btn.disabled = true;
  st.textContent = `Finding ${nFrames - 2} real intermediate structure(s) of this protein…`;
  try {
    const url = `${API}/api/morph-frames?apo=${apo}&holo=${holo}&apo_chain=${ac}&cutoff=${cutoff}` +
      `&n_frames=${nFrames}`;
    const fr = await fetch(url).then(async (r) => {
      if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || `HTTP ${r.status}`);
      return r.json();
    });
    LAST.frames = { resnums: fr.resnums, cutoff: fr.cutoff, frames: fr.frames,
      frame_labels: fr.frame_labels };
    applyConnRegion();                                 // render the real frames on the current region
    st.textContent = (fr.n_frames > 2)
      ? `Playing ${fr.n_frames} real frames: ${fr.frame_labels.join(" → ")} · ${fr.n_shared} shared residues (follows the Region selector).`
      : `No other structures of this protein found in the PDB — using apo + holo only (${fr.n_shared} shared residues).`;
  } catch (e) {
    st.textContent = `Failed: ${e.message}`;
  } finally {
    btn.disabled = false;
  }
}
$("graphapply").addEventListener("click", applyGraphMotion);
// toggling motion mode re-renders the graph on the current region (real frames if cached)
$("graphmode").addEventListener("change", () => { if (LAST.conn) applyConnRegion(); });

function matAbsPct(m, pct) {
  const v = [];
  for (const row of m) for (const x of row) v.push(Math.abs(x));
  v.sort((a, b) => a - b);
  return (v[Math.floor((pct / 100) * (v.length - 1))] || 1) + 1e-9;
}

// ── morph animation: interpolate apo→holo coords, play the coupling matrix ───
let MORPH = { data: null, t: 0, dir: 1, timer: null };

function couplingMatrix(coords, cutoff, r0) {
  const n = coords.length, W = [];
  for (let i = 0; i < n; i++) {
    const row = new Array(n).fill(0), ci = coords[i];
    for (let j = 0; j < n; j++) {
      if (i === j) continue;
      const cj = coords[j];
      const dx = ci[0] - cj[0], dy = ci[1] - cj[1], dz = ci[2] - cj[2];
      const D = Math.sqrt(dx * dx + dy * dy + dz * dz);
      if (D < cutoff && D > 1e-8) row[j] = Math.exp(-((D / r0) * (D / r0)));
    }
    W.push(row);
  }
  return W;
}

function setupMorph(d) {
  MORPH.data = d; MORPH.t = 0; MORPH.dir = 1;
  $("morphwrap").classList.remove("hidden");
  const W = couplingMatrix(d.apo_coords, d.cutoff, d.r0);
  // landmark lines persist across frames (shapes live in the layout; z updates via restyle)
  const shapes = landmarkShapes(d.resnums, d.resnums, new Set(d.active_site || []), new Set(d.drug_site || []));
  Plotly.newPlot("morphplot", [{ z: W, x: d.resnums, y: d.resnums, type: "heatmap", colorscale: "Magma", showscale: true }], {
    title: { text: "Connectivity morph apo→holo  ·  teal = active site, purple = drug", font: { size: 11, color: "#c7d0e6" }, x: 0.02 },
    margin: { l: 40, r: 10, t: 26, b: 36 }, paper_bgcolor: "#141b30", plot_bgcolor: "#141b30",
    font: { color: "#8b97b8", size: 9 }, shapes,
    xaxis: { title: "residue", showgrid: false }, yaxis: { showgrid: false, autorange: "reversed" },
  }, { displayModeBar: false, responsive: true });
  startMorph();
}

function morphFrame(t) {
  const d = MORPH.data; if (!d) return;
  const P = d.apo_coords.map((p, i) => {
    const h = d.holo_coords[i];
    return [(1 - t) * p[0] + t * h[0], (1 - t) * p[1] + t * h[1], (1 - t) * p[2] + t * h[2]];
  });
  Plotly.restyle("morphplot", { z: [couplingMatrix(P, d.cutoff, d.r0)] });
  $("morpht").textContent = `t = ${t.toFixed(2)} ${t < 0.02 ? "(apo)" : t > 0.98 ? "(holo)" : MORPH.dir > 0 ? "(→ holo)" : "(→ apo)"}`;
  $("morphslider").value = t;
}

function startMorph() {
  if (MORPH.timer) return;
  MORPH.timer = setInterval(() => {
    MORPH.t += 0.04 * MORPH.dir;
    if (MORPH.t >= 1) { MORPH.t = 1; MORPH.dir = -1; }
    else if (MORPH.t <= 0) { MORPH.t = 0; MORPH.dir = 1; }
    morphFrame(MORPH.t);
  }, 150);
  $("morphplay").textContent = "⏸ Pause";
}
function stopMorph() {
  if (MORPH.timer) { clearInterval(MORPH.timer); MORPH.timer = null; }
  $("morphplay").textContent = "▶ Play";
}
$("morphplay").addEventListener("click", () => { MORPH.timer ? stopMorph() : startMorph(); });
$("morphslider").addEventListener("input", (e) => { stopMorph(); MORPH.t = parseFloat(e.target.value); morphFrame(MORPH.t); });

init();
