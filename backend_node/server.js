const express = require("express");
const cors = require("cors");
const { dataDir } = require("./jsonStore");
const symptoms = require("./services/symptoms");

const app = express();
const port = Number(process.env.PORT || process.env.REHAB_API_PORT || 8787);

app.use(cors({
  origin: process.env.REHAB_API_ORIGIN || true,
  credentials: true,
}));
app.use(express.json({ limit: "2mb" }));

app.get("/api/health", (_req, res) => {
  res.json({
    ok: true,
    service: "rehab-ai-monitor-node-api",
    dataDir,
    time: new Date().toISOString(),
  });
});

app.get("/api/symptoms", async (req, res, next) => {
  try {
    const rows = await symptoms.listSymptoms({
      username: req.query.username,
      limit: req.query.limit,
    });
    res.json({ ok: true, data: rows });
  } catch (error) {
    next(error);
  }
});

app.post("/api/symptoms", async (req, res, next) => {
  try {
    const result = await symptoms.createSymptom(req.body);
    if (!result.ok) {
      res.status(400).json(result);
      return;
    }
    res.status(201).json(result);
  } catch (error) {
    next(error);
  }
});

app.use((req, res) => {
  res.status(404).json({ ok: false, error: `Route not found: ${req.method} ${req.path}` });
});

app.use((error, _req, res, _next) => {
  console.error("[Node API]", error);
  res.status(500).json({
    ok: false,
    error: "Internal server error",
  });
});

app.listen(port, () => {
  console.log(`[Node API] Rehab AI Monitor API listening on http://localhost:${port}`);
});
