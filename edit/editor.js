"use strict";
const $ = id => document.getElementById(id);
const clone = value => JSON.parse(JSON.stringify(value));
const title = key => key.replaceAll("_", " ").replace(/\b\w/g, char => char.toUpperCase());
const sectionNames = {hero:"Welcome message",meetings:"Meeting schedule and location",registration:"Joining and registration",contacts:"Contact people",events_intro:"Events section introduction",events:"Events and dates",homepage:"Homepage headings and descriptions",activities:"The three adventure cards",faqs:"Frequently asked questions",resources:"Calendars, guides, and resource links",about:"About Cub Scouting page"};
const draftKey = "pack12-content-draft-v1";
let model, schema, published, changed = false;
function message(text) { $("status").textContent = text; }
function errors(items) {
  $("errors").replaceChildren();
  if (!items.length) return;
  const heading = document.createElement("strong");
  heading.textContent = "Please fix these fields before downloading:";
  const list = document.createElement("ul");
  items.forEach(item => { const li = document.createElement("li"); li.textContent = item; list.append(li); });
  $("errors").append(heading, list);
  $("errors").scrollIntoView({behavior:"auto",block:"center"});
}
function problems(value, rule, path = "Website") {
  const output = [];
  const expected = rule.type;
  const actual = Array.isArray(value) ? "array" : value === null ? "null" : typeof value;
  if (actual !== expected) return [path + ": expected " + expected + "."];
  if (expected === "object") {
    for (const key of Object.keys(value)) if (!(key in rule.properties)) output.push(path + ": unknown field " + key + ".");
    for (const key of rule.required || []) if (!(key in value)) output.push(path + ": missing " + key + ".");
    for (const [key, child] of Object.entries(rule.properties)) if (key in value) output.push(...problems(value[key], child, path + " → " + title(key)));
  } else if (expected === "array") {
    if (value.length < (rule.minItems || 0) || value.length > (rule.maxItems || 500)) output.push(path + ": wrong number of entries.");
    value.forEach((item, i) => output.push(...problems(item, rule.items, path + " → entry " + (i + 1))));
  } else if (expected === "string") {
    if (value.trim().length < (rule.minLength || 0)) output.push(path + ": please fill in this field.");
    if (value.length > (rule.maxLength || 10000)) output.push(path + ": text is too long.");
    if (rule.enum && !rule.enum.includes(value)) output.push(path + ": choose a listed option.");
    if (rule.format === "date") {
      const parsed = new Date(value + "T12:00:00Z");
      if (!/^\d{4}-\d{2}-\d{2}$/.test(value) || Number.isNaN(parsed.getTime()) || parsed.toISOString().slice(0,10) !== value) output.push(path + ": choose a real date.");
    }
    if (rule.format === "time" && !/^([01]\d|2[0-3]):[0-5]\d$/.test(value)) output.push(path + ": choose a valid time.");
    if (rule.format === "email" && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) output.push(path + ": enter a valid email address.");
    if (rule.format === "link" && value) {
      if (/^https?:\/\//.test(value)) { try { const url = new URL(value); if (!url.hostname || /\s/.test(value)) throw new Error(); } catch { output.push(path + ": enter a full https:// link."); } }
      else if (!value.startsWith("./") || value.split("/").includes("..") || value.includes("\\")) output.push(path + ": use https://... or ./uploads/filename.pdf.");
      if (/[<>"]/.test(value)) output.push(path + ": the link contains an invalid character.");
    }
  }
  return output;
}
function validateContent(candidate) {
  const result = problems(candidate, schema);
  if (!result.length) {
    const keys = new Set();
    for (const item of candidate.events) {
      const key = item.title.trim().toLowerCase() + "|" + item.date;
      if (keys.has(key)) result.push("Events: duplicate " + item.title + " on " + item.date + ".");
      keys.add(key);
    }
  }
  return result;
}
function emptyValue(rule) {
  if (rule.type === "object") return Object.fromEntries(Object.entries(rule.properties).map(([key, child]) => [key, emptyValue(child)]));
  if (rule.type === "array") return [];
  if (rule.type === "boolean") return true;
  if (rule.format === "time") return "18:30";
  if (rule.enum) return rule.enum[0];
  return "";
}
function changedContent() { changed = true; message("Changes are only in this form. Download your update when you are ready."); }
function button(label, handler) { const element = document.createElement("button"); element.type = "button"; element.className = "secondary"; element.textContent = label; element.addEventListener("click",handler); return element; }
function field(container, key, rule, parent, path) {
  const value = parent[key];
  const id = path.replaceAll(".", "_");
  if (rule.type === "object") {
    const group = document.createElement("fieldset");
    const legend = document.createElement("legend"); legend.textContent = title(key);
    group.append(legend);
    for (const [child, childRule] of Object.entries(rule.properties)) field(group, child, childRule, value, path + "." + child);
    container.append(group); return;
  }
  if (rule.type === "array") {
    const list = document.createElement("div");
    const listTitle = document.createElement("h3"); listTitle.textContent = title(key); list.append(listTitle);
    list.dataset.path = path;
    value.forEach((item, index) => {
      const entry = document.createElement("div"); entry.className = "entry";
      const heading = document.createElement("h3"); heading.textContent = "Entry " + (index + 1) + (item.title ? " · " + item.title : "");
      entry.append(heading);
      for (const [child, childRule] of Object.entries(rule.items.properties)) field(entry, child, childRule, item, path + "." + index + "." + child);
      const actions = document.createElement("div"); actions.className = "entry-actions";
      if (value.length > (rule.minItems || 0)) actions.append(button("Remove entry", () => { if (confirm("Remove this entry from your draft?")) { value.splice(index,1); changedContent(); render(); } }));
      if (index > 0 && key !== "activities") actions.append(button("Move up", () => { [value[index-1],value[index]] = [value[index],value[index-1]]; changedContent(); render(); }));
      entry.append(actions); list.append(entry);
    });
    if (value.length < (rule.maxItems || 500)) list.append(button(key === "events" ? "Add event" : key === "links" ? "Add link" : "Add entry", () => { value.push(emptyValue(rule.items)); changedContent(); render(); }));
    container.append(list); return;
  }
  const wrap = document.createElement("div"); wrap.className = "field";
  const label = document.createElement("label"); label.htmlFor = id; label.textContent = rule.title ? title(rule.title) : title(key);
  let input;
  if (rule.enum) { input = document.createElement("select"); for (const choice of rule.enum) { const option = document.createElement("option"); option.value = choice; option.textContent = choice === "en" ? "English" : choice === "es" ? "Español" : choice; input.append(option); } }
  else if (rule.multiline) { input = document.createElement("textarea"); input.rows = 3; }
  else { input = document.createElement("input"); input.type = rule.type === "boolean" ? "checkbox" : ["date","time","email"].includes(rule.format) ? rule.format : "text"; }
  input.id = id; input.name = path;
  if (rule.type === "boolean") input.checked = value; else input.value = value;
  input.addEventListener("input", () => { parent[key] = rule.type === "boolean" ? input.checked : input.value; changedContent(); });
  if (rule.minLength) input.required = true;
  wrap.append(label,input);
  if (rule.description) { const hint = document.createElement("small"); hint.className = "hint"; hint.id = id + "_hint"; hint.textContent = rule.description; input.setAttribute("aria-describedby",hint.id); wrap.append(hint); }
  container.append(wrap);
}
function render() {
  const open = new Set([...document.querySelectorAll(".section[open]")].map(el => el.dataset.section));
  const first = !$("fields").children.length;
  $("fields").replaceChildren();
  for (const [key, rule] of Object.entries(schema.properties)) {
    const section = document.createElement("details"); section.className = "section"; section.dataset.section = key;
    section.open = open.has(key) || (first && ["meetings","events"].includes(key));
    const summary = document.createElement("summary"); summary.textContent = sectionNames[key] || title(key);
    const body = document.createElement("div"); body.className = "section-content";
    if (rule.type === "object") for (const [child, childRule] of Object.entries(rule.properties)) field(body,child,childRule,model[key],key+"."+child);
    else field(body,key,rule,model,key);
    section.append(summary,body); $("fields").append(section);
  }
}
$("content-form").addEventListener("submit", event => event.preventDefault());
$("download").addEventListener("click", () => {
  const issues = validateContent(model); errors(issues); if (issues.length) return;
  const objectURL = URL.createObjectURL(new Blob([JSON.stringify(model,null,2)+"\n"],{type:"application/json"}));
  const anchor = document.createElement("a"); anchor.href = objectURL; anchor.download = "site.json"; anchor.click(); setTimeout(() => URL.revokeObjectURL(objectURL),10000);
  message("Update downloaded. Upload site.json to GitHub’s content folder, then commit. Your live site has not changed yet.");
});
$("save-draft").addEventListener("click", () => {
  try { localStorage.setItem(draftKey,JSON.stringify({content:model,base:published,savedAt:new Date().toISOString()})); message("Draft saved on this device. It is not published."); }
  catch { message("This browser could not save a draft. Download your update instead."); }
});
$("restore-draft").addEventListener("click", () => {
  try {
    const saved = JSON.parse(localStorage.getItem(draftKey) || "null");
    if (!saved) { message("There is no saved draft on this device."); return; }
    const issues = validateContent(saved.content); errors(issues); if (issues.length) return;
    model = clone(saved.content); render(); changed = true;
    message(JSON.stringify(saved.base) !== JSON.stringify(published) ? "Draft restored. The published site changed since this draft started. Compare with the current website before uploading to avoid overwriting someone else’s changes." : "Draft restored. It is not published.");
  } catch { message("Could not restore this draft. Import a downloaded site.json instead."); }
});
$("reset").addEventListener("click", () => { if (changed && !confirm("Discard form changes and reload the published content?")) return; location.reload(); });
$("import-file").addEventListener("change", async event => {
  const file = event.target.files[0]; if (!file) return;
  try { const candidate = JSON.parse(await file.text()); const issues = validateContent(candidate); errors(issues); if (issues.length) return; model = clone(candidate); changed = true; render(); message("Update file imported. Review it, then download when ready."); }
  catch { errors(["That file could not be read. Choose a site.json downloaded from this editor."]); }
});
async function start() {
  try {
    const responses = await Promise.all([fetch("../content/site.json",{cache:"no-store"}),fetch("../content/editor-schema.json",{cache:"no-store"})]);
    if (responses.some(response => !response.ok)) throw new Error("Content files did not load.");
    [published,schema] = await Promise.all(responses.map(response => response.json()));
    const issues = validateContent(published); if (issues.length) throw new Error(issues.join(" "));
    model = clone(published); render(); $("download").disabled = false; $("save-draft").disabled = false;
    message("Current website content loaded. Make changes below; nothing goes live until you upload and commit.");
  } catch { message("The editor could not load. Open this page through the published website or a local web server. If the problem continues, ask the repository maintainer to check content/site.json."); }
}
start();
