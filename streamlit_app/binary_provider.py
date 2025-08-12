# binary_provider.py
import os, json, tarfile, hashlib, urllib.request, urllib.error
from pathlib import Path
from typing import Optional

def _first_writable(cands):
    for p in cands:
        try:
            p.mkdir(parents=True, exist_ok=True)
            t = p / ".write_test"
            t.write_text("ok", encoding="utf-8")
            t.unlink(missing_ok=True)
            return p
        except Exception:
            pass
    raise RuntimeError("No writable data directory found")

def select_data_dir() -> Path:
    env_dir = os.getenv("MCMC_DATA_DIR")
    cands = []
    if env_dir:
        cands.append(Path(env_dir))
    cands.append(Path("/mount/data/mcmc"))            # Streamlit Cloud
    cands.append(Path.home() / ".cache" / "mcmc")     # lokal
    cands.append(Path(".mcmc_data"))                  # Projekt-Fallback
    return _first_writable(cands)

def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def _http_json(url: str, timeout=10):
    req = urllib.request.Request(url, headers={"User-Agent": "mcmc-app/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))

def _resolve_release_asset(owner: str, repo: str, tag: str, asset_name: str) -> str:
    if tag.lower() != "latest":
        return f"https://github.com/{owner}/{repo}/releases/download/{tag}/{asset_name}"
    # latest via GitHub API (ohne Token, public)
    api = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    data = _http_json(api)
    for a in data.get("assets", []):
        if a.get("name") == asset_name and a.get("browser_download_url"):
            return a["browser_download_url"]
    raise RuntimeError(f"Asset '{asset_name}' not found in latest release")

def get_mcmc_path() -> Path:
    """
    Einheitliche Bezugsquelle:
    1) MCMC_PATH (falls gesetzt) → direkt nutzen
    2) Sonst Download/Cache unter DATA_DIR/bin
    - Steuertag: MCMC_RELEASE_TAG (z.B. v0.1.2 oder latest)
    - Besitzt Tag-Caching (.release_tag)
    """
    # 0) Fester Override → ideal für ECS/EC2, wenn du /opt/mcmc/bin/mcmc vorinstallierst
    override = os.getenv("MCMC_PATH")
    if override and os.access(override, os.X_OK):
        return Path(override)

    owner = os.getenv("MCMC_RELEASE_OWNER", "elisastph")
    repo  = os.getenv("MCMC_RELEASE_REPO",  "MCMC")
    tag   = os.getenv("MCMC_RELEASE_TAG",   "v0.1.2")  # oder "latest"
    asset = os.getenv("MCMC_RELEASE_ASSET", "mcmc-linux-x86_64.tar.gz")
    sha   = os.getenv("MCMC_RELEASE_SHA256", "")       # optional

    data_dir = select_data_dir()
    bin_dir  = data_dir / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)

    exe = bin_dir / "mcmc"
    tag_file = bin_dir / ".release_tag"

    # Tag-Caching: nur neu laden, wenn exe fehlt oder Tag wechselt
    cached_tag = tag_file.read_text(encoding="utf-8").strip() if tag_file.exists() else ""
    if exe.exists() and os.access(exe, os.X_OK) and cached_tag == tag:
        return exe

    # URL bestimmen (inkl. latest-Auflösung)
    url = _resolve_release_asset(owner, repo, tag, asset)

    # Download
    tar_path = bin_dir / "mcmc.tar.gz"
    req = urllib.request.Request(url, headers={"User-Agent": "mcmc-app/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r, tar_path.open("wb") as f:
        f.write(r.read())

    # optional: Checksum
    if sha:
        got = _sha256_file(tar_path)
        if got.lower() != sha.lower():
            tar_path.unlink(missing_ok=True)
            raise RuntimeError(f"SHA256 mismatch: expected {sha}, got {got}")

    # Entpacken (vorher alte exe entfernen)
    try:
        exe.unlink(missing_ok=True)
        with tarfile.open(tar_path, "r:gz") as tf:
            tf.extractall(bin_dir)
        exe.chmod(0o755)
    finally:
        tar_path.unlink(missing_ok=True)

    if not exe.exists():
        raise FileNotFoundError("mcmc not found after extraction")

    tag_file.write_text(tag, encoding="utf-8")
    return exe

def get_paths():
    d = select_data_dir()
    return {
        "DATA_DIR": d,
        "BIN_DIR": d / "bin",
        "RESULTS_DIR": d / "results",
        "ANALYSIS_DIR": d / "analysis_results" / "visualize_lattice",
    }
