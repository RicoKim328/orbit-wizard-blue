"""Bundle the Astropy parts used for satellite coordinate transforms.

The upstream hook imports every Astropy subpackage, including optional plotting
code whose import can require matplotlib. This app uses no Astropy plotting.
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata


def _required_module(name: str) -> bool:
    parts = name.split(".")
    return not any(part in {"tests", "test", "conftest", "visualization"} for part in parts)


datas = collect_data_files("astropy") + copy_metadata("astropy") + copy_metadata("numpy")
datas += [entry for entry in collect_data_files("astropy", include_py_files=True)
          if entry[0].endswith(("_parsetab.py", "_lextab.py"))]

hiddenimports = ["numpy.lib.recfunctions"]
excludedimports = ["astropy.visualization", "pytest"]
for package in ("astropy.constants", "astropy.coordinates", "astropy.time", "astropy.units", "astropy.utils.iers",
                "astropy.table", "astropy.io.ascii"):
    hiddenimports += collect_submodules(package, filter=_required_module, on_error="warn once")
