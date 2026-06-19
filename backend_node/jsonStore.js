const fs = require("node:fs/promises");
const path = require("node:path");

const repoRoot = path.resolve(__dirname, "..");
const dataDir = process.env.REHAB_DATA_DIR
  ? path.resolve(process.env.REHAB_DATA_DIR)
  : path.join(repoRoot, "database");

function dataPath(fileName) {
  return path.join(dataDir, fileName);
}

async function readJson(fileName, fallback) {
  try {
    const raw = await fs.readFile(dataPath(fileName), "utf8");
    return JSON.parse(raw);
  } catch (error) {
    if (error && error.code === "ENOENT") return fallback;
    throw error;
  }
}

async function writeJson(fileName, value) {
  await fs.mkdir(dataDir, { recursive: true });
  const target = dataPath(fileName);
  const tmp = `${target}.tmp-${process.pid}-${Date.now()}`;
  await fs.writeFile(tmp, `${JSON.stringify(value, null, 2)}\n`, "utf8");
  await fs.rename(tmp, target);
}

module.exports = {
  dataDir,
  dataPath,
  readJson,
  writeJson,
};
