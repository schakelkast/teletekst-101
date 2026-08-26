"""Teletekst-HTML omzetten naar bruikbare platte tekst.

De NOS levert een pagina als HTML: spans met kleurklassen, links om
paginanummers heen, en tekens uit de private-use-range F020-F07F voor de
blokgrafiek. Dat laatste is beeld, geen tekst — een schermlezer of een
spraakassistent moet er niets mee.
"""

from __future__ import annotations

import re
from html import unescape
from html.parser import HTMLParser

# De blokgrafiek van teletekst zit in dit bereik. Het zijn tekeningen, geen
# letters, dus in platte tekst worden het spaties: zo blijft de kolomindeling
# staan zonder dat er onzin in de tekst komt.
MOZAIEK = re.compile(r"[\uf020-\uf07f]")

# Regels die alleen uit opvulling bestaan, of het NOS-kader zelf.
_LEEG = re.compile(r"^[\s\-_=]*$")


class _Stripper(HTMLParser):
    """Haalt de tags eruit en houdt alleen de tekst over."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stukken: list[str] = []

    def handle_data(self, data: str) -> None:
        self.stukken.append(data)

    def resultaat(self) -> str:
        return "".join(self.stukken)


def naar_regels(content: str, houd_leeg: bool = False) -> list[str]:
    """Zet de HTML van een pagina om in een lijst regels platte tekst.

    Args:
        content: het `content`-veld uit het antwoord van de NOS.
        houd_leeg: lege regels behouden. Standaard gaan ze eruit, want die
            komen vooral uit de blokgrafiek en zeggen niets.
    """
    if not content:
        return []

    p = _Stripper()
    p.feed(content)
    plat = p.resultaat()

    regels = []
    for regel in plat.split("\n"):
        regel = MOZAIEK.sub(" ", unescape(regel))
        regel = regel.replace("\xa0", " ").rstrip()
        if not houd_leeg and _LEEG.match(regel):
            continue
        regels.append(regel.strip() if not houd_leeg else regel)
    return regels


def naar_tekst(content: str) -> str:
    """De hele pagina als één stuk tekst, geschikt voor spraak of een melding."""
    return "\n".join(naar_regels(content))


def _is_banner(regel: str) -> bool:
    """Herkent kopbalken als 'S P O R T' of 'J  O  U  R  N  A  A  L'.

    Teletekst spatieert zulke titels uit om ze groot te laten lijken. Als
    samenvatting van een pagina zeggen ze niets, dus die slaan we over. Een
    gewone kop in hoofdletters zoals 'VERWACHTING TOT MORGENNACHT' blijft wel
    staan: die is niet uitgespatieerd.
    """
    kaal = regel.strip()
    if not kaal or any(c.islower() for c in kaal):
        return False
    return kaal.count(" ") / len(kaal) > 0.4


def kop(content: str) -> str:
    """De eerste betekenisvolle regel, bruikbaar als toestandswaarde.

    Korte rubriekwoorden als 'hoofdpunten' krijgen geen voorkeur: er wordt
    eerst gezocht naar een regel die echt iets vertelt.
    """
    bruikbaar = []
    for regel in naar_regels(content):
        # De koptekst 'NOS Teletekst 101' zegt niets over de inhoud.
        if regel.lower().startswith("nos teletekst"):
            continue
        if _is_banner(regel) or len(regel) <= 3:
            continue
        bruikbaar.append(regel)

    for regel in bruikbaar:
        if len(regel) > 12:
            return regel[:250]
    return bruikbaar[0][:250] if bruikbaar else ""


def paginaverwijzingen(content: str) -> list[str]:
    """Alle paginanummers waar deze pagina naar doorverwijst."""
    return sorted({m for m in re.findall(r'href="#(\d{3}(?:-\d+)?)"', content or "")})
