"""Bewaakt dat schermen en namen ook echt een vertaling hebben.

Een ontbrekende vertaling breekt niets in de code, maar de gebruiker ziet dan
een kale sleutel als `component.nos_teletekst.options.step.snel_weer.title` in
plaats van een zin. Dat merk je alleen als je toevallig dat scherm opent - en
precies zulke fouten kwamen hier al twee keer pas bij de gebruiker aan het licht.
"""

import ast
import json
from pathlib import Path

import pytest

MAP = Path(__file__).resolve().parents[1] / "custom_components" / "nos_teletekst"
TALEN = ["nl", "en"]


def _vertaling(taal: str) -> dict:
    return json.loads((MAP / "translations" / f"{taal}.json").read_text("utf-8"))


def _toont_scherm(functie: ast.AST) -> bool:
    """Toont deze stap iets aan de gebruiker?

    Een stap die meteen opslaat en terugkeert heeft geen tekst nodig; alleen
    stappen met een formulier of een menu komen daadwerkelijk in beeld.
    """
    for n in ast.walk(functie):
        if isinstance(n, ast.Attribute) and n.attr in (
            "async_show_form",
            "async_show_menu",
        ):
            return True
    return False


def _stappen() -> tuple[set[str], set[str]]:
    """Alle stapnamen die een scherm tonen, gesplitst in config en options."""
    boom = ast.parse((MAP / "config_flow.py").read_text("utf-8"))
    config: set[str] = set()
    options: set[str] = set()
    for klasse in [n for n in ast.walk(boom) if isinstance(n, ast.ClassDef)]:
        doel = options if "Options" in klasse.name else config
        for n in ast.walk(klasse):
            if (
                isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                and n.name.startswith("async_step_")
                and _toont_scherm(n)
            ):
                doel.add(n.name[len("async_step_") :])
    return config, options


def _alle_stapnamen() -> set[str]:
    """Elke async_step, ook de stappen die niets tonen."""
    boom = ast.parse((MAP / "config_flow.py").read_text("utf-8"))
    return {
        n.name[len("async_step_") :]
        for n in ast.walk(boom)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        and n.name.startswith("async_step_")
    }


@pytest.mark.parametrize("taal", TALEN)
def test_elke_stap_heeft_een_scherm(taal):
    config, options = _stappen()
    v = _vertaling(taal)
    mist_config = config - set(v.get("config", {}).get("step", {}))
    mist_options = options - set(v.get("options", {}).get("step", {}))
    assert not mist_config, (
        f"{taal}: config-stappen zonder tekst: {sorted(mist_config)}"
    )
    assert not mist_options, (
        f"{taal}: options-stappen zonder tekst: {sorted(mist_options)}"
    )


@pytest.mark.parametrize("taal", TALEN)
def test_menukeuzes_wijzen_naar_bestaande_stappen(taal):
    """Een menu dat naar een onbekende stap wijst geeft een lege pagina."""
    v = _vertaling(taal)
    options = _alle_stapnamen()
    for naam, stap in v.get("options", {}).get("step", {}).items():
        for keuze in stap.get("menu_options", {}):
            assert keuze in options, (
                f"{taal}: menu '{naam}' verwijst naar onbekende stap '{keuze}'"
            )


@pytest.mark.parametrize("taal", TALEN)
def test_entiteitsnamen_zijn_vertaald(taal):
    """Elke translation_key in de code hoort een naam te hebben."""
    v = _vertaling(taal).get("entity", {})
    ontbreekt = []
    for bestand in ("sensor.py", "binary_sensor.py", "image.py"):
        platform = bestand.removesuffix(".py")
        boom = ast.parse((MAP / bestand).read_text("utf-8"))
        for n in ast.walk(boom):
            gevonden = None
            if isinstance(n, ast.Assign):
                for t in n.targets:
                    naam = getattr(t, "attr", getattr(t, "id", None))
                    if naam == "_attr_translation_key" and isinstance(
                        n.value, ast.Constant
                    ):
                        gevonden = n.value.value
            if gevonden and gevonden not in v.get(platform, {}):
                ontbreekt.append(f"{platform}.{gevonden}")
    assert not ontbreekt, f"{taal}: entiteiten zonder naam: {sorted(set(ontbreekt))}"


def test_beide_talen_hebben_dezelfde_sleutels():
    """Anders mist de ene taal een scherm dat de andere wel heeft."""

    def sleutels(d, pad=""):
        uit = set()
        for k, val in d.items():
            hier = f"{pad}.{k}" if pad else k
            uit.add(hier)
            if isinstance(val, dict):
                uit |= sleutels(val, hier)
        return uit

    nl, en = sleutels(_vertaling("nl")), sleutels(_vertaling("en"))
    assert not nl - en, f"alleen in nl: {sorted(nl - en)}"
    assert not en - nl, f"alleen in en: {sorted(en - nl)}"


@pytest.mark.parametrize("taal", TALEN)
def test_geen_lege_teksten(taal):
    """Een lege vertaling is net zo verwarrend als een ontbrekende."""

    def loop(d, pad=""):
        for k, val in d.items():
            hier = f"{pad}.{k}" if pad else k
            if isinstance(val, dict):
                loop(val, hier)
            else:
                assert str(val).strip(), f"{taal}: {hier} is leeg"

    loop(_vertaling(taal))
