# PyInstaller specification for the double-clickable simulator.
#
# Run from the repository root, after building the interface:
#     cd web && npm run build && cd ..
#     pyinstaller packaging/monte-carlo-simulator.spec
#
# The interface is bundled as plain files, so a React build costs nothing more
# than Jinja templates would: PyInstaller carries either as data.
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

ROOT = Path(SPECPATH).resolve().parent

datas = [
    # Served by the same process — this is what makes it a single executable.
    (str(ROOT / "web" / "dist"), "web/dist"),
    # The blank workbook offered by /api/template.
    (str(ROOT / "data" / "templates"), "data/templates"),
]

# uvicorn resolves its protocol and lifespan implementations by name at runtime,
# so static analysis cannot see them and they must be named explicitly.
hiddenimports = [
    *collect_submodules("uvicorn"),
    "uvicorn.logging",
    "uvicorn.loops.auto",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan.on",
    # Imported by the app module string, never referenced from the launcher.
    "monte_carlo_simulator.web_api",
]

analysis = Analysis(
    [str(ROOT / "src" / "monte_carlo_simulator" / "launcher.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    # Matplotlib's interactive backends pull in GUI toolkits the server never
    # uses; the figures it writes go through the Agg backend.
    excludes=["tkinter", "PyQt5", "PyQt6", "PySide2", "PySide6", "IPython", "jupyter"],
    noarchive=False,
)

pyz = PYZ(analysis.pure)

exe = EXE(
    pyz,
    analysis.scripts,
    analysis.binaries,
    analysis.datas,
    [],
    name="MonteCarloSimulator",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    # The consultant starts a desktop-style application: the local server stays
    # invisible and the browser opens only once its health endpoint answers.
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
