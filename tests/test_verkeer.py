"""Tests voor het uitlezen van de verkeersinformatie.

Draaien zonder Home Assistant en zonder internet:

    python -m pytest tests -q
"""

import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1] / "custom_components" / "nos_teletekst")
)

import verkeer  # noqa: E402

# Zoals de regels van pagina 730 binnenkomen: meldingen lopen over meerdere
# regels door en beginnen met een streepje.
REGELS = [
    "NOS Teletekst 730",
    "binnenland   1/6",
    "VERKEERSINFORMATIE",
    "actueel            26 aug. 21:40 uur",
    "Files:",
    "- A12 Duitse grens->Arnhem tussen knp.",
    "Oud-Dijk en Duiven 3 km,2 min.,",
    "wegwerkzaamheden,de rechterrijstrook",
    "is dicht.",
    "- A2 Utrecht->Den Bosch tussen Everdingen",
    "en Culemborg 12 km,15 min.,ongeval.",
    "Afsluiting/Omleiding:",
    "- N57 Middelburg->Brouwersdam bij afrit",
    "Serooskerke wegwerkzaamheden,dicht.",
    "Bron:ANWB",
    "nieuws  binnenland  buitenland  sport",
]


def test_meldingen_worden_samengevoegd():
    """Een melding loopt over meerdere regels door en hoort er weer een te zijn."""
    m = verkeer.lees(REGELS)
    assert len(m) == 3
    assert "rechterrijstrook" in m[0]["tekst"]


def test_kopregels_tellen_niet_mee():
    for m in verkeer.lees(REGELS):
        assert "VERKEERSINFORMATIE" not in m["tekst"]
        assert not m["tekst"].startswith("Bron:")


def test_weg_richting_lengte_en_vertraging():
    eerste = verkeer.lees(REGELS)[0]
    assert eerste["weg"] == "A12"
    assert eerste["van"] == "Duitse grens"
    assert eerste["naar"] == "Arnhem"
    assert eerste["km"] == 3
    assert eerste["minuten"] == 2


def test_richting_stopt_bij_bij():
    """'N57 Middelburg->Brouwersdam bij afrit ...' eindigt bij 'bij'."""
    laatste = verkeer.lees(REGELS)[-1]
    assert laatste["naar"] == "Brouwersdam"


def test_soort_scheidt_files_van_afsluitingen():
    m = verkeer.lees(REGELS)
    assert verkeer.is_file(m[0]) is True
    assert verkeer.is_file(m[-1]) is False


def test_samenvatting_telt_alleen_files():
    s = verkeer.samenvatting(verkeer.lees(REGELS))
    assert s["aantal_files"] == 2
    assert s["totaal_km"] == 15
    assert s["totaal_minuten"] == 17


def test_wegen_op_nummer_gesorteerd():
    """A2 hoort voor A12 te staan, niet erachter."""
    s = verkeer.samenvatting(verkeer.lees(REGELS))
    assert s["wegen"] == ["A2", "A12", "N57"]


def test_lege_invoer_klapt_niet():
    assert verkeer.lees([]) == []
    assert verkeer.samenvatting([])["aantal_files"] == 0
