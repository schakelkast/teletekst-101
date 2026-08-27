"""Tests voor het omzetten van een pagina naar een rooster met kleuren.

Het tekenen zelf vraagt Pillow; die tests slaan we over als het er niet is.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1] / "custom_components" / "nos_teletekst")
)

import render

EENVOUDIG = '<span class="yellow">AB</span>\n<span class="blue bg-blue">CD</span>'


def test_rooster_is_altijd_40_bij_25():
    """Teletekst is een vast raster; korte regels worden aangevuld."""
    r = render.naar_rooster(EENVOUDIG)
    assert len(r) == render.REGELS
    assert all(len(rij) == render.KOLOMMEN for rij in r)


def test_kleur_van_de_span_wordt_overgenomen():
    r = render.naar_rooster(EENVOUDIG)
    teken, voor, achter = r[0][0]
    assert teken == "A"
    assert voor == render.KLEUREN["yellow"]
    assert achter == render.KLEUREN["black"]


def test_achtergrondkleur_wordt_herkend():
    r = render.naar_rooster(EENVOUDIG)
    _, voor, achter = r[1][0]
    assert voor == render.KLEUREN["blue"]
    assert achter == render.KLEUREN["blue"]


def test_kleur_valt_terug_na_de_span():
    r = render.naar_rooster('<span class="red">A</span>B')
    assert r[0][0][1] == render.KLEUREN["red"]
    assert r[0][1][1] == render.KLEUREN["white"]


def test_te_lange_regel_wordt_afgekapt():
    r = render.naar_rooster("X" * 60)
    assert len(r[0]) == render.KOLOMMEN


def test_lege_invoer_geeft_leeg_rooster():
    r = render.naar_rooster("")
    assert len(r) == render.REGELS
    assert r[0][0][0] == " "


def test_tekenen_geeft_een_png():
    pytest.importorskip("PIL")
    png = render.teken(EENVOUDIG, hoogte=250)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"


def test_breed_beeld_is_vier_op_drie():
    Image = pytest.importorskip("PIL.Image")
    import io

    im = Image.open(io.BytesIO(render.teken(EENVOUDIG, hoogte=250, breed=True)))
    assert abs(im.width / im.height - 4 / 3) < 0.02
