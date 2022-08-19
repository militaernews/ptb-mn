import random
from dataclasses import dataclass
from typing import List

import numpy as numpy
import svgwrite
from dotenv import load_dotenv

load_dotenv()

ENTRIES = [
    "Israel",
    "Baerbock verurteilt",
    "Lauterbach warnt",
    "China",
    "wirkungsvoll",
    "Biden",
    "Schwurbler",
    "böse NATO",
    "Wunderwaffe",
    "Lindner verspricht",
    "SDF/YPG",
    "Hartz IV",
    "Atomkrieg",
    "kampferprobt",
    "Spinner",
    "Weltmacht",
    "Kokain",
    "Entnazifizieren",
    "HIMARS",
    "Krim",
    "Russland droht",
    "Biolabor",
    "Schlangeninsel",
    "Faschist",
    "Nazi",
    "Britischer Geheimdienst",
    "Azov",
    "Alina",
    "Erdogan",
    "Korruption",
    "Konvention",
    "Lufthohheit",
    "Taiwan",
    "Frontverlauf",
    "Kinzhal",
    "Meinung",
    "Lukashenko",
    "Impfung",
    "Reichsbürger",
    "Trump",
    "Schwarzmarkt",
    "einsatzbereit",
    "Putin macht bald ernst",
    "Militärexperte",
    "Zweiter Weltkrieg",
    "Palästina",
    "Verluste",
    "Logistik",
    "Stalingrad",
    "Barbarossa",
    "Wehrmacht",
    "Unfall",
    "Ivan",
    "NATO-Osterweiterung",
    "Vorstoß",
    "T-14",
    "Armata",
    "Kämpf doch selbst",
    "Propaganda",
    "Taliban",
    "Wahrheit",
    "Aber die USA",
    "Ukraine beschießt Zivilisten",
    "Munitionsdepot",
    "Selenski fordert",
    "Man muss verhandeln",
    "Gas",
    "Bayraktar-TB2",
    "Quelle?",
    "Hostomel",
    "Elite",
    "8 Jahre",
    "Genozid",
    "seit 2014"
]


@dataclass
class BingoField:
    text: str
    checked: bool = False


def generate_bingo_field():
    random.shuffle(ENTRIES)

    outer = list()

    #   for x in range(1, 4):
    #
    #     inner = list()
    #    for y in range(1, 4):
    #       inner.append(BingoField(ENTRIES[x + y]))
    #
    # outer.append(inner)

    for x in range(1, 5 * 5, 5):
        inner = list()
        print(x)

        for y in ENTRIES[x:x + 5]:
            print(y)
            inner.append(BingoField(y))

        outer.append(inner)

    print(outer)
    return outer


def check_win(fields: List[List[BingoField]]):
    # horizontal condition
    for row in fields:
        if all(item.checked for item in row):
            return True

    # vertical condition
    for column in zip(*fields):
        if all(item.checked for item in column):
            return True

    return False


def set_checked(word: str, fields: List[List[BingoField]]):
    print(list(numpy.array(fields).flat))
    for item in list(numpy.array(fields).flat):
        if item.text == word:
            item.checked = True
            print("check")


# "<text style='font-size:3.175px;fill:#000000;stroke-width:0.264583' x='42.4465' y='32.978203' id='text277'>Test2</text>"

dwg = svgwrite.Drawing('test.svg', profile='tiny', size=(600, 600))
dwg.add(dwg.line((0, 0), (100, 40), stroke=svgwrite.rgb(10, 10, 16, '%')))
dwg.add(dwg.text('Test', insert=(0, 8), fill='red'))
dwg.save()

canvas_size = 1080

svg = f"""<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<svg
   width='{canvas_size}'
   height='{canvas_size}'
   viewBox='0 0 {canvas_size} {canvas_size}'
   version='1.1'
   xmlns='http://www.w3.org/2000/svg'
   xmlns:svg='http://www.w3.org/2000/svg'>"""

field_size = 3
line_width = 6
width_treshold = int((canvas_size - ((field_size - 1) * line_width)) / field_size + line_width)
current_width = width_treshold

while current_width < canvas_size:
    print(current_width)
    svg += f"""
    <rect
       style="fill:#1884cc;fill-opacity:1"
       width="{canvas_size}"
       height="6"
       x="0"
       y="{current_width - line_width}" />
    <rect
       style="fill:#1884cc;fill-opacity:1"   
       width="6"
       height="{canvas_size}"
       x="{current_width - line_width}"
       y="0" />
"""
    current_width += width_treshold


print("lines done, now text -----------------")



svg += "</svg>"

print(svg)
