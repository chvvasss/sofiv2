"""
Star S - Astronomy Workspace Setup Script
==========================================
Run this after cloning the repository to set up the full environment:

    python setup.py

This will:
1. Create a Python virtual environment (.venv)
2. Install all required packages
3. Download TOPCAT, STILTS, and portable OpenJDK
4. Generate template files (FITS, VOTable)
5. Run verification tests
"""
import os
import platform
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TOOLS = ROOT / "tools"
JAVA_DIR = TOOLS / "java"
TEMPLATES = ROOT / "templates"

# Download URLs
TOPCAT_URL = "http://www.starlink.ac.uk/topcat/topcat-full.jar"
STILTS_URL = "http://www.starlink.ac.uk/stilts/stilts.jar"
ADOPTIUM_API = "https://api.adoptium.net/v3/binary/latest/21/ga/{os}/{arch}/jre/hotspot/normal/eclipse"


def print_step(msg):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}\n")


def get_venv_python():
    if platform.system() == "Windows":
        return ROOT / ".venv" / "Scripts" / "python.exe"
    return ROOT / ".venv" / "bin" / "python"


def get_venv_pip():
    if platform.system() == "Windows":
        return ROOT / ".venv" / "Scripts" / "pip.exe"
    return ROOT / ".venv" / "bin" / "pip"


def create_venv():
    print_step("1/5 - Creating Python virtual environment")
    venv_path = ROOT / ".venv"
    if venv_path.exists():
        print("  .venv already exists, skipping...")
        return
    subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
    print("  .venv created successfully")


def install_packages():
    print_step("2/5 - Installing Python packages")
    pip = str(get_venv_pip())
    subprocess.run([pip, "install", "--upgrade", "pip"], check=True)
    subprocess.run([pip, "install", "-r", str(ROOT / "requirements.txt")], check=True)
    print("  All packages installed")


def download_file(url, dest, description):
    dest = Path(dest)
    if dest.exists() and dest.stat().st_size > 1000:
        print(f"  {dest.name} already exists, skipping...")
        return

    print(f"  Downloading {description}...")
    try:
        urllib.request.urlretrieve(url, str(dest))
        size_mb = dest.stat().st_size / 1024 / 1024
        print(f"  {dest.name}: {size_mb:.1f} MB downloaded")
    except Exception as e:
        # Fallback: try with requests if urllib fails
        try:
            python = str(get_venv_python())
            subprocess.run(
                [python, "-c", f"""
import requests
r = requests.get("{url}", stream=True, timeout=120)
r.raise_for_status()
with open(r"{dest}", "wb") as f:
    for chunk in r.iter_content(8192):
        f.write(chunk)
"""],
                check=True,
            )
            size_mb = dest.stat().st_size / 1024 / 1024
            print(f"  {dest.name}: {size_mb:.1f} MB downloaded (via requests)")
        except Exception as e2:
            print(f"  WARNING: Failed to download {description}: {e2}")
            print(f"  Please download manually from: {url}")
            print(f"  Save to: {dest}")


def download_tools():
    print_step("3/5 - Downloading TOPCAT, STILTS & Java")

    TOOLS.mkdir(parents=True, exist_ok=True)
    JAVA_DIR.mkdir(parents=True, exist_ok=True)

    # TOPCAT & STILTS
    download_file(TOPCAT_URL, TOOLS / "topcat-full.jar", "TOPCAT (~31 MB)")
    download_file(STILTS_URL, TOOLS / "stilts.jar", "STILTS (~16 MB)")

    # Check if Java already extracted
    java_dirs = [d for d in JAVA_DIR.iterdir() if d.is_dir() and d.name.startswith("jdk")]
    if java_dirs:
        print(f"  Java JRE already exists: {java_dirs[0].name}, skipping...")
        return

    # Determine OS and arch for Adoptium API
    os_name = platform.system().lower()
    machine = platform.machine().lower()

    if os_name == "windows":
        os_api = "windows"
    elif os_name == "darwin":
        os_api = "mac"
    else:
        os_api = "linux"

    if machine in ("x86_64", "amd64"):
        arch_api = "x64"
    elif machine in ("aarch64", "arm64"):
        arch_api = "aarch64"
    else:
        arch_api = "x64"

    jre_url = ADOPTIUM_API.format(os=os_api, arch=arch_api)
    jre_zip = JAVA_DIR / "openjdk-jre.zip"

    download_file(jre_url, jre_zip, f"OpenJDK 21 JRE for {os_api}/{arch_api} (~50 MB)")

    if jre_zip.exists():
        print("  Extracting Java JRE...")
        with zipfile.ZipFile(str(jre_zip), "r") as z:
            z.extractall(str(JAVA_DIR))
        jre_zip.unlink()

        # Find extracted directory name and update BAT scripts
        for item in JAVA_DIR.iterdir():
            if item.is_dir() and item.name.startswith("jdk"):
                print(f"  Extracted: {item.name}")
                update_bat_scripts(item.name)
                break


def update_bat_scripts(jre_dirname):
    """Update BAT scripts with the actual JRE directory name."""
    for bat_name in ("topcat.bat", "stilts.bat"):
        bat_path = TOOLS / bat_name
        if bat_path.exists():
            content = bat_path.read_text()
            # Replace any existing jdk-* pattern with the actual dirname
            import re
            updated = re.sub(r"jdk-[\w.+\-]+", jre_dirname, content)
            bat_path.write_text(updated)


def generate_templates():
    print_step("4/5 - Generating template files (FITS, VOTable)")
    python = str(get_venv_python())
    script = ROOT / "scripts" / "create_template_fits.py"
    subprocess.run([python, str(script)], check=True)


def run_tests():
    print_step("5/5 - Running verification tests")
    python = str(get_venv_python())
    result = subprocess.run([python, str(ROOT / "tests" / "test_packages.py")])

    # Also test STILTS if available
    java_dirs = [d for d in JAVA_DIR.iterdir() if d.is_dir() and d.name.startswith("jdk")] if JAVA_DIR.exists() else []
    stilts_jar = TOOLS / "stilts.jar"
    csv_template = TEMPLATES / "star_catalog_template.csv"

    if java_dirs and stilts_jar.exists() and csv_template.exists():
        java_bin = java_dirs[0] / "bin" / ("java.exe" if platform.system() == "Windows" else "java")
        print("\nSTILTS format tests:")
        for fmt, path in [
            ("csv", TEMPLATES / "star_catalog_template.csv"),
            ("fits", TEMPLATES / "star_catalog_template.fits"),
            ("votable", TEMPLATES / "star_catalog_template.vot"),
        ]:
            if path.exists():
                r = subprocess.run(
                    [str(java_bin), "-jar", str(stilts_jar), "tpipe", f"in={path}", f"ifmt={fmt}", "omode=count"],
                    capture_output=True, text=True,
                )
                status = "OK" if r.returncode == 0 else "FAILED"
                print(f"  {fmt.upper()}: {status} - {r.stdout.strip()}")

    return result.returncode


def main():
    print("=" * 60)
    print("  Star S - Astronomy Workspace Setup")
    print(f"  Python {sys.version.split()[0]} | {platform.system()} {platform.machine()}")
    print("=" * 60)

    create_venv()
    install_packages()
    download_tools()
    generate_templates()
    exit_code = run_tests()

    print("\n" + "=" * 60)
    if exit_code == 0:
        print("  Setup complete! All tests passed.")
    else:
        print("  Setup complete with some test failures. Check output above.")
    print("=" * 60)

    print(f"""
Next steps:
  1. Activate the virtual environment:
     {"source .venv/Scripts/activate" if platform.system() == "Windows" else "source .venv/bin/activate"}

  2. Launch TOPCAT (GUI):
     {"tools\\topcat.bat" if platform.system() == "Windows" else "tools/topcat.sh"}

  3. Open the analysis notebook:
     jupyter notebook notebooks/analysis.ipynb
""")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
