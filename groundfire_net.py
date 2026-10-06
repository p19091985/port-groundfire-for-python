"""Compatibility loader for the vendored ``groundfire_net`` package.

The editable source lives in ``groundfire-online-service/src/groundfire_net``.
Repository-root commands use the synchronized copy in ``versao-python``.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


_PACKAGE_DIR = Path(__file__).resolve().parent / "versao-python" / "groundfire_net"
_PACKAGE_INIT = _PACKAGE_DIR / "__init__.py"
_SPEC = importlib.util.spec_from_file_location(
    __name__,
    _PACKAGE_INIT,
    submodule_search_locations=[str(_PACKAGE_DIR)],
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"unable to load groundfire_net from {_PACKAGE_INIT}")

_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules[__name__] = _MODULE
_SPEC.loader.exec_module(_MODULE)
globals().update(_MODULE.__dict__)
