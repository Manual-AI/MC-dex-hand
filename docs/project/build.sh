#!/usr/bin/env bash
# Assemble the paper site and the existing simulation under the same Pages project.
set -eu
repo=$(cd "$(dirname "$0")/../.." && pwd)
mkdir -p "${1:?Pass the destination directory for the static site}"
site=$(cd "$1" && pwd)
cd "$repo"
mkdir -p "$site"/{bowl/media,paper,downloads}

cp docs/project/paper.css "$site/"
cp -R docs/project/media docs/project/vendor "$site/"
cp docs/paper/mc-dex-hand-neurips2026.pdf "$site/paper/"
# Keep the displayed and downloadable citations in sync with the repository.
python3 - "$site" <<'CITATION'
from html import escape
from pathlib import Path
import sys

site = Path(sys.argv[1])
readme = Path("README.md").read_text()
citation = readme.split("\n```bibtex\n", 1)[1].split("\n```", 1)[0]
template = Path("docs/project/index.html").read_text()
(site / "index.html").write_text(template.replace("<!-- paper-citation -->", escape(citation)))
(site / "paper/citation.bib").write_text(citation + "\n")
CITATION

cd simulation/browser
cp -R assets licenses vendor *.js *.css "$site/"
cp bowl/index.html bowl/*.js bowl/*.json bowl/*.xml bowl/*.css "$site/bowl/"
cp bowl/media/bowl-policy.mp4 "$site/bowl/media/"
cp ../LICENSE ../NOTICE "$site/licenses/"
zip -q -j "$site/downloads/MC-Dex-Bowl.zip" bowl/MC-Dex-Bowl.html
