const { readJson, writeJson } = require("../jsonStore");

const SYMPTOMS_FILE = "patient_symptoms.json";

function normalize(value) {
  return String(value == null ? "" : value).trim().replace(/\s+/g, " ");
}

function parseVas(value) {
  const parsed = Number.parseInt(String(value).replace(",", "."), 10);
  if (!Number.isFinite(parsed)) return -1;
  return Math.max(0, Math.min(10, parsed));
}

function latestFirst(records) {
  return [...records].sort((a, b) => {
    const av = String(a.created_at || a.date || a.time || "");
    const bv = String(b.created_at || b.date || b.time || "");
    return bv.localeCompare(av);
  });
}

async function listSymptoms({ username, limit = 20 } = {}) {
  const data = await readJson(SYMPTOMS_FILE, []);
  const records = Array.isArray(data) ? data : [];
  const target = normalize(username).toLowerCase();
  const filtered = target
    ? records.filter((item) => normalize(item && item.username).toLowerCase() === target)
    : records;
  return latestFirst(filtered).slice(0, Number(limit) || 20);
}

function validateSymptom(payload) {
  const body = payload && typeof payload === "object" ? payload : {};
  const username = normalize(body.username);
  const fullName = normalize(body.full_name || body.fullName || username);
  const symptoms = normalize(body.symptoms || body.description);
  const painLocation = normalize(body.pain_location || body.painLocation);
  const exercise = normalize(body.exercise);
  const dateValue = normalize(body.date);
  const vas = parseVas(body.vas);

  if (!username) return { error: "username is required" };
  if (vas < 0) return { error: "vas must be a number from 0 to 10" };
  if (!symptoms) return { error: "symptoms is required" };
  if (symptoms.length < 6) return { error: "symptoms is too short" };

  const now = new Date();
  const viDate = new Intl.DateTimeFormat("vi-VN", {
    timeZone: "Asia/Bangkok",
    hour: "2-digit",
    minute: "2-digit",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(now).replace(",", " -");

  return {
    record: {
      username,
      full_name: fullName,
      symptoms,
      pain_location: painLocation,
      exercise,
      vas,
      date: dateValue || now.toISOString().slice(0, 10),
      time: viDate,
      created_at: now.toISOString(),
      source: "node_api_patient_form",
    },
  };
}

async function createSymptom(payload) {
  const validation = validateSymptom(payload);
  if (validation.error) return { ok: false, error: validation.error };
  const data = await readJson(SYMPTOMS_FILE, []);
  const records = Array.isArray(data) ? data : [];
  records.push(validation.record);
  await writeJson(SYMPTOMS_FILE, records);
  return { ok: true, record: validation.record };
}

module.exports = {
  listSymptoms,
  createSymptom,
  validateSymptom,
};
