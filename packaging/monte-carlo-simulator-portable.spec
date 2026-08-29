# PyInstaller specification for the portable Windows distribution.
#
# Unlike the historical one-file build, this profile keeps the interpreter,
# native libraries and application data in a directory next to the launchers.
# The whole directory can be zipped and copied to a clean Windows x64 machine;
# Python, Node.js and the project packages are not required on that machine.
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules, copy_metadata


ROOT = Path(SPECPATH).resolve().parent

datas = [
    (str(ROOT / "web" / "dist"), "web/dist"),
    (str(ROOT / "data" / "templates"), "data/templates"),
]

# Keep package metadata available to libraries that query their installed
# version or optional features at runtime.
for distribution in (
    "fastapi",
    "matplotlib",
    "numpy",
    "openpyxl",
    "pandas",
    "pydantic",
    "scipy",
    "starlette",
    "uvicorn",
):
    datas += copy_metadata(distribution)

# Uvicorn and the ASGI stack select implementations by name at runtime. Those
# imports are invisible to static analysis, so collect them explicitly. The
# Agg backend is the only Matplotlib backend used by the exported charts.
hiddenimports = sorted(
    {
        *collect_submodules("uvicorn"),
        *collect_submodules("fastapi"),
        *collect_submodules("starlette"),
        *collect_submodules("pydantic"),
        "matplotlib.backends.backend_agg",
        "monte_carlo_simulator.web_api",
        "multipart",
        "python_multipart",
        "uvicorn.lifespan.on",
        "uvicorn.logging",
        "uvicorn.loops.auto",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets.auto",
    }
)

analysis = Analysis(
    [str(ROOT / "src" / "monte_carlo_simulator" / "launcher.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "PyQt5", "PyQt6", "PySide2", "PySide6", "IPython", "jupyter"],
    noarchive=False,
)

pyz = PYZ(analysis.pure)

# A single console-enabled launcher starts, diagnoses and stops RiskSim. Keeping
# one executable prevents mixed launcher generations in a portable directory.
risksim_exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="RiskSim",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

portable = COLLECT(
    risksim_exe,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    name="RiskSim-Portable",
)
