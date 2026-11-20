(() => {
"use strict";
const $ = id => document.getElementById(id);
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const S = { file: null, result: null, accepted: new Set(), letter: "", tab: "match" };

fetch("/api/industries").then(r => r.json()).then(list => {
  for (const g of list) if (g.id !== "general") $("industry").insertAdjacentHTML("beforeend", `<option value="${esc(g.id)}">${esc(g.label)}</option>`);
});

$("sample").onclick = async () => {
  const d = await (await fetch("/api/sample")).json();
  S.file = null; $("fileName").textContent = ""; $("cv").value = d.cv; $("job").value = d.job;
};
const takeFile = f => { if (!f) return; S.file = f; $("fileName").textContent = "Selected: " + f.name; $("cv").value = ""; };
$("file").onchange = e => takeFile(e.target.files[0]);
const drop = $("drop");
["dragenter", "dragover"].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.add("over"); }));
["dragleave", "drop"].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.remove("over"); }));
drop.addEventListener("drop", e => takeFile(e.dataTransfer.files[0]));
$("cv").oninput = () => { if ($("cv").value.trim()) { S.file = null; $("fileName").textContent = ""; } };

$("run").onclick = async () => {
  const fd = new FormData();
  if (S.file) fd.append("cv_file", S.file); else fd.append("cv_text", $("cv").value);
  fd.append("job_text", $("job").value); fd.append("industry", $("industry").value); fd.append("lang", $("lang").value);
  $("run").disabled = true; $("status").textContent = "Analyzing…";
  try {
    const r = await fetch("/api/analyze", { method: "POST", body: fd });
    const data = await r.json();
    if (!r.ok) throw new Error(data.error || "Request failed");
    S.result = data; S.accepted = new Set(data.suggestions.map((_, i) => i)); S.letter = data.cover_letter;
    $("status").textContent = ""; render();
  } catch (e) { $("status").textContent = e.message; }
  finally { $("run").disabled = false; }
};

document.querySelector(".tabs").onclick = e => {
  const b = e.target.closest("button[data-t]"); if (!b) return;
  S.tab = b.dataset.t;
  document.querySelectorAll(".tabs button").forEach(x => x.setAttribute("aria-selected", String(x === b)));
  render();
};

function tailored() {
  const r = S.result, map = new Map();
  r.suggestions.forEach((s, i) => { if (S.accepted.has(i)) map.set(s.line, s.improved); });
  const out = [];
  for (const l of r.cv_lines) { if (l.heading && out.length) out.push(""); out.push(map.get(l.index) ?? l.text); }
  return out.join("\n");
}

const LABEL = { required: "Required", other: "Also mentioned", preferred: "Nice to have" };
function render() {
  const r = S.result, p = $("pane");
  if (!r) return;
  $("nSug").textContent = r.suggestions.length;
  $("nChk").textContent = r.checks.filter(c => c.level !== "ok").length;
  if (S.tab === "match") {
    const m = r.match;
    const groups = ["required", "other", "preferred"].map(k => {
      const ts = m.terms.filter(t => t.importance === k);
      if (!ts.length) return "";
      return `<h3>${LABEL[k]} · ${ts.filter(t => t.found).length}/${ts.length}</h3><div class="chips">${ts.map(t =>
        `<span class="chip ${t.found ? "ok" : "miss"}" title="${esc(t.found ? "In your CV as: " + t.cv_forms.join(", ") : "Not found in your CV")}">${t.found ? "✓" : "✗"} ${esc(t.job_form)}${t.found && t.cv_forms[0] && t.cv_forms[0].toLowerCase() !== t.job_form.toLowerCase() ? ` <small>(${esc(t.cv_forms[0])})</small>` : ""}</span>`).join("")}</div>`;
    }).join("");
    p.innerHTML = `<div class="score"><div class="ring" style="--p:${m.score}"><b>${m.score}%</b></div>
      <div><b>${esc(r.job.role || "Job")}${r.job.company ? " · " + esc(r.job.company) : ""}</b>
      <div class="hint">Weighted match using the <b>${esc(m.industry_label)}</b> glossary. Required skills count 3×, nice-to-have 1×.
      Required skills covered: ${m.required_score}%.</div></div></div>${groups || '<p class="hint">No glossary terms found in the job ad. Try another glossary.</p>'}
      <p class="hint" style="margin-top:14px">Only add missing skills you really have.</p>`;
    return;
  }
  if (S.tab === "changes") {
    if (!r.suggestions.length) { p.innerHTML = `<div class="empty">No rule-based changes for this CV.</div>`; }
    else p.innerHTML = `<div class="row" style="justify-content:space-between;margin-bottom:10px"><span class="hint">${S.accepted.size} of ${r.suggestions.length} accepted</span>
      <span class="row"><button class="btn quiet sm" data-all="1">Accept all</button><button class="btn quiet sm" data-all="0">Reject all</button></span></div>
      ${r.suggestions.map((s, i) => `<div class="sug ${S.accepted.has(i) ? "on" : ""}"><label><input type="checkbox" data-i="${i}" ${S.accepted.has(i) ? "checked" : ""}> Line ${s.line + 1} · ${esc(s.rules.join(", "))}</label>
        <div class="old">${esc(s.original)}</div><div class="new">${esc(s.improved)}</div><div class="why">${esc(s.reason)}</div></div>`).join("")}`;
    p.insertAdjacentHTML("beforeend", `<h3>Tailored CV</h3><textarea class="out" id="cvOut"></textarea>
      <div class="row" style="margin-top:10px">${r.upload_id ? '<button class="btn sm" data-x="pdf-original">PDF (original layout)</button>' : ""}
      <button class="btn ${r.upload_id ? "ghost" : ""} sm" data-x="pdf">PDF (plain)</button><button class="btn ghost sm" data-x="docx">Word</button></div>`);
    $("cvOut").value = tailored();
    p.querySelectorAll("input[data-i]").forEach(c => c.onchange = () => { const i = +c.dataset.i; c.checked ? S.accepted.add(i) : S.accepted.delete(i); render(); });
    p.querySelectorAll("button[data-all]").forEach(b => b.onclick = () => { S.accepted = new Set(b.dataset.all === "1" ? r.suggestions.map((_, i) => i) : []); render(); });
    bindExports("cv", () => $("cvOut").value);
    return;
  }
  if (S.tab === "checks") {
    p.innerHTML = r.checks.map(c => `<div class="chk"><span class="lvl ${c.level}">${c.level}</span><div>${esc(c.message)}${
      c.lines && c.lines.length ? `<div class="why">${c.lines.slice(0, 5).map(i => esc(r.cv_lines[i].text)).join("<br>")}${c.lines.length > 5 ? "<br>…" : ""}</div>` : ""}</div></div>`).join("");
    return;
  }
  p.innerHTML = `<p class="hint">A template filled with your matched skills and your own CV lines. Edit it before sending.</p>
    <textarea class="out" id="letterOut"></textarea><div class="row" style="margin-top:10px"><button class="btn sm" data-x="pdf">PDF</button><button class="btn ghost sm" data-x="docx">Word</button></div>`;
  $("letterOut").value = S.letter; $("letterOut").oninput = e => S.letter = e.target.value;
  bindExports("letter", () => $("letterOut").value);
}

function bindExports(kind, getText) {
  $("pane").querySelectorAll("button[data-x]").forEach(b => b.onclick = async () => {
    const fmt = b.dataset.x, body = { kind, format: fmt, text: getText() };
    if (fmt === "pdf-original") {
      body.upload_id = S.result.upload_id; body.replacements = {};
      S.result.suggestions.forEach((s, i) => { if (S.accepted.has(i)) body.replacements[s.original] = s.improved; });
    }
    const r = await fetch("/api/export", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    if (!r.ok) { $("status").textContent = (await r.json()).error || "Export failed"; return; }
    if (fmt === "pdf-original" && +r.headers.get("X-Skipped")) $("status").textContent = r.headers.get("X-Skipped") + " change(s) could not be placed in the original PDF.";
    const a = document.createElement("a"); a.href = URL.createObjectURL(await r.blob());
    a.download = (kind === "cv" ? "CV-tailored" : "Cover-letter") + (fmt === "docx" ? ".docx" : ".pdf");
    document.body.append(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
  });
}
})();
