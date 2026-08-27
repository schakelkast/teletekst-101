"""Bewaakt dat elke gebruikte naam ook echt geimporteerd is.

Aanleiding: `CONF_EIGEN` werd gebruikt in config_flow.py maar stond niet in de
import. Dat viel niet op, want de regel wordt pas uitgevoerd als je op
"Eigen sensor verwijderen" klikt - en dan geeft Home Assistant een 500 zonder
zichtbare uitleg. Een NameError hoort bij het bouwen op te vallen, niet bij de
gebruiker.
"""

import ast
import builtins
from pathlib import Path

import pytest

MAP = Path(__file__).resolve().parents[1] / "custom_components" / "nos_teletekst"
MODULES = sorted(p.name for p in MAP.glob("*.py"))

# Namen die Python zelf aanlevert of die uit een with/except-blok komen.
EXTRA = {"self", "annotations", "__file__", "__name__", "__doc__"}


def _beschikbaar(boom: ast.Module) -> set[str]:
    """Alles wat in deze module een naam krijgt: import, toekenning, def, arg."""
    # In een testmodule is __builtins__ een dict, dus expliciet de module.
    namen: set[str] = set(dir(builtins)) | EXTRA
    for n in ast.walk(boom):
        if isinstance(n, ast.ImportFrom):
            namen |= {a.asname or a.name for a in n.names}
        elif isinstance(n, ast.Import):
            namen |= {(a.asname or a.name).split(".")[0] for a in n.names}
        elif isinstance(n, ast.Lambda):
            a = n.args
            namen |= {x.arg for x in a.args + a.kwonlyargs + a.posonlyargs}
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            namen.add(n.name)
            a = n.args
            namen |= {x.arg for x in a.args + a.kwonlyargs + a.posonlyargs}
            if a.vararg:
                namen.add(a.vararg.arg)
            if a.kwarg:
                namen.add(a.kwarg.arg)
        elif isinstance(n, ast.ClassDef):
            namen.add(n.name)
        elif isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
            namen.add(n.id)
        elif isinstance(n, ast.ExceptHandler) and n.name:
            namen.add(n.name)
        elif isinstance(n, (ast.Global, ast.Nonlocal)):
            namen |= set(n.names)
        elif isinstance(n, ast.comprehension):
            namen |= {
                t.id for t in ast.walk(n.target) if isinstance(t, ast.Name)
            }
    return namen


@pytest.mark.parametrize("naam", MODULES)
def test_geen_onbekende_namen(naam):
    boom = ast.parse((MAP / naam).read_text("utf-8"))
    beschikbaar = _beschikbaar(boom)
    gebruikt = {
        n.id
        for n in ast.walk(boom)
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)
    }
    ontbreekt = sorted(gebruikt - beschikbaar)
    assert not ontbreekt, f"{naam} gebruikt namen die nergens vandaan komen: {ontbreekt}"
