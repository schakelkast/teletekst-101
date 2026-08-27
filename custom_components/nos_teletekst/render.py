"""Een teletekstpagina tekenen als afbeelding.

Daarmee is teletekst ook buiten een dashboard bruikbaar: meesturen in een
melding, op een e-ink schermpje zetten, of in een gewone plaatjeskaart tonen.

De pagina komt binnen als HTML met spans die de kleur bepalen en tekens uit de
private-use-range F020-F07F voor de blokgrafiek. Die tekens zitten in het
meegeleverde teletekstfont, dus het beeld wordt hetzelfde als op tv.
"""

from __future__ import annotations

import io
from html.parser import HTMLParser
from pathlib import Path

KOLOMMEN = 40
REGELS = 25

# De acht teletekstkleuren.
KLEUREN = {
    "black": (0, 0, 0),
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "yellow": (255, 255, 0),
    "blue": (0, 0, 255),
    "magenta": (255, 0, 255),
    "cyan": (0, 255, 255),
    "white": (255, 255, 255),
}
VOORGROND = KLEUREN["white"]
ACHTERGROND = KLEUREN["black"]

FONT = Path(__file__).parent / "frontend" / "Android_VeraMono.ttf"


class _Rooster(HTMLParser):
    """Zet de HTML om in een rooster van tekens met hun kleuren."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rijen: list[list[tuple[str, tuple, tuple]]] = [[]]
        self._stapel: list[tuple[tuple, tuple]] = [(VOORGROND, ACHTERGROND)]

    def _kleuren_uit(self, attrs) -> tuple[tuple, tuple]:
        voor, achter = self._stapel[-1]
        for naam, waarde in attrs:
            if naam != "class" or not waarde:
                continue
            for klasse in waarde.split():
                if klasse.startswith("bg-") and klasse[3:] in KLEUREN:
                    achter = KLEUREN[klasse[3:]]
                elif klasse in KLEUREN:
                    voor = KLEUREN[klasse]
        return voor, achter

    def handle_starttag(self, tag: str, attrs) -> None:
        self._stapel.append(self._kleuren_uit(attrs))

    def handle_endtag(self, tag: str) -> None:
        if len(self._stapel) > 1:
            self._stapel.pop()

    def handle_data(self, data: str) -> None:
        voor, achter = self._stapel[-1]
        for teken in data:
            if teken == "\n":
                self.rijen.append([])
            else:
                self.rijen[-1].append((teken, voor, achter))


def naar_rooster(content: str) -> list[list[tuple[str, tuple, tuple]]]:
    """Lees de pagina uit tot een rooster van 40 bij 25."""
    p = _Rooster()
    p.feed(content or "")
    rijen = p.rijen[:REGELS]
    while len(rijen) < REGELS:
        rijen.append([])
    for rij in rijen:
        del rij[KOLOMMEN:]
        while len(rij) < KOLOMMEN:
            rij.append((" ", VOORGROND, ACHTERGROND))
    return rijen


def teken(content: str, hoogte: int = 500, breed: bool = True) -> bytes:
    """Teken de pagina en geef hem terug als PNG.

    Args:
        content: het `content`-veld uit het antwoord van de NOS.
        hoogte: gewenste hoogte in beeldpunten.
        breed: op tv zijn de tekens breder dan op nos.nl. Met `True` wordt het
            beeld horizontaal opgerekt tot 4:3, net als de kaart doet.

    """
    from PIL import Image, ImageDraw, ImageFont

    # De celmaat volgt uit het font zelf, zodat de blokgrafiek naadloos
    # aansluit: precies een regelhoogte hoog en een tekenbreedte breed.
    grootte = max(8, round(hoogte / REGELS / 1.2037))
    font = ImageFont.truetype(str(FONT), grootte)
    opgaand, neergaand = font.getmetrics()
    celhoogte = opgaand + neergaand
    celbreedte = round(font.getlength("M"))

    afbeelding = Image.new(
        "RGB", (KOLOMMEN * celbreedte, REGELS * celhoogte), ACHTERGROND
    )
    tekenaar = ImageDraw.Draw(afbeelding)

    for r, rij in enumerate(naar_rooster(content)):
        y = r * celhoogte
        for k, (teken_, voor, achter) in enumerate(rij):
            x = k * celbreedte
            if achter != ACHTERGROND:
                tekenaar.rectangle(
                    [x, y, x + celbreedte - 1, y + celhoogte - 1], fill=achter
                )
            if teken_ != " ":
                tekenaar.text(
                    (x, y + opgaand), teken_, font=font, fill=voor, anchor="ls"
                )

    if breed:
        # 40x25 tekens op een 4:3-beeld: de cel is dan 0,833 breed tegenover
        # hoog, terwijl het font 0,50 geeft.
        afbeelding = afbeelding.resize(
            (round(afbeelding.height * 4 / 3), afbeelding.height),
            Image.Resampling.LANCZOS,
        )

    uit = io.BytesIO()
    afbeelding.save(uit, format="PNG", optimize=True)
    return uit.getvalue()
