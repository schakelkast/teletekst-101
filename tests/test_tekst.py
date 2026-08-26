"""Tests voor het omzetten van teletekst-HTML naar tekst.

Deze tests draaien zonder Home Assistant en zonder internet: `tekst.py` gebruikt
alleen de standaardbibliotheek. Draaien met:

    python -m pytest tests -q
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components" / "nos_teletekst"))

import tekst  # noqa: E402

VASTE_PAGINA = json.loads((Path(__file__).parent / "pagina101.json").read_text("utf-8"))
INHOUD = VASTE_PAGINA["content"]


def test_blokgrafiek_wordt_geen_tekst():
    """F020-F07F is beeld. Die tekens mogen nooit in de tekst belanden."""
    plat = tekst.naar_tekst(INHOUD)
    assert not any("\uf020" <= c <= "\uf07f" for c in plat)


def test_geen_html_meer_over():
    plat = tekst.naar_tekst(INHOUD)
    assert "<span" not in plat
    assert "&#x" not in plat
    assert "</a>" not in plat


def test_regels_zijn_leesbaar():
    regels = tekst.naar_regels(INHOUD)
    assert len(regels) > 5
    assert any("NOS Teletekst" in r for r in regels)


def test_kop_slaat_uitgespatieerde_titels_over():
    """'J  O  U  R  N  A  A  L' is een sierkop, geen samenvatting."""
    assert tekst.kop(INHOUD) not in ("", None)
    assert "  " not in tekst.kop(INHOUD).strip()[:12]


@pytest.mark.parametrize(
    "regel,verwacht",
    [
        ("J  O  U  R  N  A  A  L", True),
        ("S P O R T", True),
        ("VERWACHTING TOT MORGENNACHT", False),
        ("Gewone kop met kleine letters", False),
    ],
)
def test_bannerherkenning(regel, verwacht):
    assert tekst._is_banner(regel) is verwacht


def test_koppen_hebben_tekst_en_paginanummer():
    koppen = tekst.koppen(INHOUD)
    assert koppen, "pagina 101 is een indexpagina en hoort koppen te bevatten"
    for k in koppen:
        assert k["tekst"]
        assert k["pagina"][:3].isdigit()


def test_koppen_bevatten_geen_menuregels():
    """'nieuws     101   sport' is een menu, geen kop."""
    for k in tekst.koppen(INHOUD):
        assert "  " not in k["tekst"] or not any(c.isdigit() for c in k["tekst"])


def test_jaartal_is_geen_paginanummer():
    """'copyright N O S 2026' verwijst niet naar pagina 026."""
    koppen = tekst.koppen('<span>copyright N O S  2026</span>')
    assert koppen == []


def test_subpagina_krijgt_streepje():
    """Teletekst schrijft 649/1, de API verwacht 649-1."""
    koppen = tekst.koppen("<span>Botic van de Zandschulp schittert 649/1</span>")
    assert koppen == [{"tekst": "Botic van de Zandschulp schittert", "pagina": "649-1"}]


def test_verwijzingen_zijn_uniek_en_gesorteerd():
    v = tekst.paginaverwijzingen(INHOUD)
    assert v == sorted(set(v))
    assert all(p[:3].isdigit() for p in v)


def test_lege_invoer_klapt_niet():
    assert tekst.naar_regels("") == []
    assert tekst.naar_tekst("") == ""
    assert tekst.kop("") == ""
    assert tekst.koppen("") == []
    assert tekst.paginaverwijzingen(None) == []
