"""Package the existing bowl app, worker and licensed assets as a double-clickable HTML file."""

import argparse
import base64
import gzip
from html import escape
import json
from pathlib import Path
import subprocess

BOWL = Path(__file__).resolve().parent
BROWSER = BOWL.parent
ROOT = BROWSER.parents[1]
DEST = BOWL / "MC-Dex-Bowl.html"

ASSETS = {
    "./scene.xml": "application/xml",
    "./objects.json": "application/json",
    "./actor.json": "application/json",
    "../assets/kinematics.json": "application/json",
    "../assets/appearance.json": "application/json",
    "../assets/meshes.tar.gz": "application/gzip",
    "../vendor/mujoco.wasm": "application/wasm",
    "./media/bowl-policy.mp4": "video/mp4",
}

# Blob URLs let the page and its module worker consume the same in-memory files.
BOOT = """
try {
  const archive = JSON.parse(document.getElementById("bowl-files").textContent);
  const files = Object.create(null);
  const workerAssets = Object.create(null);
  for (const [name, {mime, gzip, data}] of Object.entries(archive)) {
    const bytes = Uint8Array.from(atob(data), ch => ch.charCodeAt(0));
    let blob = new Blob([bytes], {type: mime});
    if (gzip) {
      const stream = blob.stream().pipeThrough(new DecompressionStream("gzip"));
      blob = new Blob([await new Response(stream).arrayBuffer()], {type: mime});
    }
    files[name] = URL.createObjectURL(blob);
    if (!name.endsWith(".js") && name !== "./actor.json" && !name.endsWith(".mp4")) {
      workerAssets[name] = blob;
    }
  }
  document.getElementById("bowl-files").remove();
  const workerSource = await (await fetch(files["./worker.js"])).text();
  // A local file and a worker can have different opaque origins. Send the actual
  // Blobs so the worker can mint URLs in its own origin before starting MuJoCo.
  const init = `self.onmessage = ({ data }) => {
    const urls = Object.fromEntries(Object.entries(data).map(([k, b]) => [k, URL.createObjectURL(b)]));
    globalThis.mcDexBundle = {urls};
    (async () => {`;
  const worker = new Blob([init, workerSource, "\\n})(); };"], {type: "text/javascript"});
  const workerURL = URL.createObjectURL(worker);
  globalThis.mcDexBundle = {urls: files, createPreviewWorker() {
    const thread = new Worker(workerURL);
    thread.postMessage(workerAssets);
    return thread;
  }};
  document.querySelector("a.back").href = files["./media/bowl-policy.mp4"];
  await import(files["./app.js"]);
} catch (error) {
  document.getElementById("status").textContent = "Could not open the demo";
  document.getElementById("notice").textContent = error.message;
  throw error;
}
"""


def pack(data, mime):
    compressed = gzip.compress(data, compresslevel=9, mtime=0)
    use_gzip = len(compressed) < 0.95 * len(data)
    payload = compressed if use_gzip else data
    return dict(
        mime=mime, gzip=use_gzip, data=base64.b64encode(payload).decode("ascii")
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--esbuild", default="esbuild", help="Path to esbuild 0.25.11")
    args = parser.parse_args()
    files = {
        name: pack((BOWL / name).read_bytes(), mime) for name, mime in ASSETS.items()
    }
    for name in ("./app.js", "./worker.js"):
        # Only the loader's unused Node.js branches import these built-ins.
        result = subprocess.run(
            [
                args.esbuild,
                name,
                "--bundle",
                "--format=esm",
                "--platform=browser",
                "--target=es2022",
                "--minify",
                *(
                    ["--define:import.meta.url=self.location.href"]
                    if name == "./worker.js"
                    else []
                ),
                "--external:module",
                "--external:worker_threads",
            ],
            cwd=BOWL,
            check=True,
            stdout=subprocess.PIPE,
        )
        files[name] = pack(result.stdout, "text/javascript")

    page = (BOWL / "index.html").read_text()
    for name in ("../style.css", "./bowl.css"):
        link = f'<link rel="stylesheet" href="{name}" />'
        assert link in page
        page = page.replace(link, "<style>" + (BOWL / name).read_text() + "</style>")
    page = page.replace('href="./media/bowl-policy.mp4"', 'href="#recorded-throws"')
    notices = [
        ROOT / "simulation/LICENSE",
        ROOT / "simulation/NOTICE",
        *sorted((BROWSER / "licenses").iterdir()),
    ]
    text = "\n\n".join(f"{p.name}\n\n{p.read_text()}" for p in notices)
    page = page.replace(
        "</footer>",
        "</footer>\n<details><summary>Licenses and notices</summary>"
        '<pre style="white-space:pre-wrap;overflow-wrap:anywhere">'
        + escape(text)
        + "</pre></details>",
    )
    entry = '<script type="module" src="./app.js"></script>'
    assert entry in page
    # The embedded JSON contains only MIME strings, known paths, booleans and Base64.
    page = page.replace(
        entry,
        '<script type="application/json" id="bowl-files">'
        + json.dumps(files, separators=(",", ":"))
        + "</script>\n"
        + '<script type="module">'
        + BOOT
        + "</script>",
    )
    DEST.write_text(page, encoding="utf-8")
    print(f"Wrote {DEST.name} ({DEST.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
