"""Tests voor de eigen sensoren."""

import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1] / "custom_components" / "nos_teletekst")
)

import eigen  # noqa: E402

REGELS = [
    "NOS Teletekst 702",
    "VERWACHTING TOT MORGENNACHT:     1/2",
    "De Bilt 21 graden, buien",
    "Maastricht 23 graden",
    "waterstand Lobith 8,42 meter",
]


def test_regel_op_nummer_telt_vanaf_een():
    d = {"manier": "regel", "regel": 3}
    assert eigen.lees(REGELS, d) == "De Bilt 21 graden, buien"


def test_regel_buiten_bereik_geeft_niets():
    assert eigen.lees(REGELS, {"manier": "regel", "regel": 99}) is None


def test_zoeken_pakt_de_eerste_treffer():
    d = {"manier": "zoek", "zoekwoord": "graden"}
    assert eigen.lees(REGELS, d) == "De Bilt 21 graden, buien"


def test_zoeken_is_hoofdletterongevoelig():
    assert eigen.lees(REGELS, {"manier": "zoek", "zoekwoord": "DE BILT"}) is not None


def test_alleen_het_getal():
    d = {"manier": "zoek", "zoekwoord": "De Bilt", "alleen_getal": True}
    assert eigen.lees(REGELS, d) == 21


def test_komma_wordt_een_kommagetal():
    d = {"manier": "zoek", "zoekwoord": "Lobith", "alleen_getal": True}
    assert eigen.lees(REGELS, d) == 8.42


def test_geen_getal_in_de_regel():
    d = {"manier": "zoek", "zoekwoord": "buien", "alleen_getal": True}
    # 21 staat in dezelfde regel, dus die wordt gevonden
    assert eigen.lees(REGELS, d) == 21
    d2 = {"manier": "regel", "regel": 1, "alleen_getal": True}
    assert eigen.lees(REGELS, d2) == 702


def test_niets_gevonden_geeft_niets():
    assert eigen.lees(REGELS, {"manier": "zoek", "zoekwoord": "sneeuw"}) is None
    assert eigen.lees([], {"manier": "regel", "regel": 1}) is None


def test_sleutel_is_bruikbaar_als_id():
    assert eigen.sleutel({"naam": "Temperatuur De Bilt"}) == "temperatuur_de_bilt"
    assert eigen.sleutel({"naam": ""}) == "eigen"


def test_regelnummer_telt_ook_lege_regels_mee():
    """Op het scherm tel je rijen, niet 'regels met tekst erop'.

    Zou de lege regel wegvallen, dan wijst regel 3 naar 'C' in plaats van naar
    de lege regel, en krijgt de gebruiker iets anders dan hij aanwees.
    """
    met_leeg = ["A", "B", "", "C"]
    assert eigen.lees(met_leeg, {"manier": "regel", "regel": 3}) == ""
    assert eigen.lees(met_leeg, {"manier": "regel", "regel": 4}) == "C"
