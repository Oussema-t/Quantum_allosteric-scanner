// Cleveland Clinic Quantum Allosteric Scanner — Team AuraQu
// Data-foundation build: load + complete + visualize (no quantum prediction yet).
const API = ""; // same origin (served by FastAPI)

const $ = (id) => document.getElementById(id);
let TARGETS = [];
const LAST = { view: null, intel: null };

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

  const sourceRaw = $("source").value.trim();
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
  if (src === "none" || !n) {
    note.textContent = "Active site: none found for this protein (UniProt has no annotation; no ligand pocket).";
    note.classList.add("error");
  } else {
    note.classList.remove("error");
    note.textContent = `Active site: ${SITE_SOURCE_LABEL[src] || src} — ${n} residues. ${data.active_site_detail || ""}`;
    if (!$("source").value.trim()) $("source").value = (data.active_site || []).join(",");
  }
}

// Enter in the PDB or Chain field loads the structure immediately
["pdb", "chains"].forEach((id) =>
  $(id).addEventListener("keydown", (e) => {
    if (e.key === "Enter") { e.preventDefault(); loadAndVisualize(); }
  }));

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
function render3D() {
  const data = LAST.view;
  if (!data) return;
  const el = $("viewer");
  if (!viewer) viewer = $3Dmol.createViewer(el, { backgroundColor: "#ffffff" });
  viewer.clear();

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
