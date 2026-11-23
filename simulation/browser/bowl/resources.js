// The standalone page supplies in-memory URLs for the same release files.
export function resourceURL(path) {
  return globalThis.mcDexBundle?.urls[path] ?? new URL(path, import.meta.url).href;
}

export function createPreviewWorker() {
  if (globalThis.mcDexBundle) return globalThis.mcDexBundle.createPreviewWorker();
  return new Worker(resourceURL("./worker.js"), { type: "module" });
}
