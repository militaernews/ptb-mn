import random
from dataclasses import dataclass
from typing import List

import numpy as numpy
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
    "HartzIV",
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
    "NATO Osterweiterung",
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


rrr = generate_bingo_field()

all_width = 2500
all_height = 2500

svg = f"""<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<svg
   width='{all_width}'
   height='{all_height}'
   viewBox='0 0 {all_width} {all_height}'
   version='1.1'
   xmlns='http://www.w3.org/2000/svg'
   xmlns:svg='http://www.w3.org/2000/svg'>"""

canvas_width = 1920
canvas_height = 1080
field_size = 5
line_width = 6
height_treshold = int((canvas_height - (field_size * line_width)) / field_size + line_width)
width_treshold = int((canvas_width - (
            field_size * line_width)) / field_size + line_width)  # int((canvas_size - ((field_size - 1) * line_width)) / field_size + line_width)
current_width = 0

svg_field = f"<svg width=\"{canvas_width}\" height=\"{canvas_height}\"  x=\"%50\" dy=\"1em\">"

field_counter = 0
curr_x = 0

while current_width < canvas_width:
    print(current_width)

    x_var = f"<svg width=\"{width_treshold}\" height=\"{height_treshold}\"  x=\"{current_width}\""
    current_height = 0
    curr_y = 0

    while current_height < canvas_height:
        print(current_height)

        curr_field = rrr[curr_x][curr_y]
        print(curr_field)

        textss = curr_field.text.split(" ")
        if len(textss)==1:
            inner_text = f"""<tspan  x="50%" text-anchor="middle">{textss[0]}</tspan>"""
        elif len(textss)==2:
            inner_text = f"""<tspan  x="50%" text-anchor="middle" dy="1em" transform="translate(0 -1em)">{textss[1]}</tspan><tspan  x="50%" text-anchor="middle" dy="-1em">{textss[0]}</tspan>"""
        elif len(textss) == 3:
            inner_text = f"""<tspan  x="50%" text-anchor="middle">{textss[1]}</tspan><tspan  x="50%" text-anchor="middle" dy="1em">{textss[2]}</tspan><tspan  x="50%" text-anchor="middle" dy="-2em">{textss[0]}</tspan>"""
        else:
            inner_text = "TOO LONG"

        svg_field += f"""
        {x_var} y="{current_height}" text-align="center">
       <rect x="0" y="0" width="100%" height="100%"   stroke="#1884cc" stroke-width="6px"  stroke-location="inside"  fill="#2a1a3f" />
       <text y="50%" font-size="48px" font-family="Arial" dominant-baseline="middle" fill="white" >{inner_text}</text>
     </svg>
"""
        curr_y += 1
        current_height += height_treshold
    curr_x+=1
    current_width += width_treshold

print("lines done, now text -----------------")

svg_field += "</svg>"

svg += svg_field

svg += f"""
<text dy="1em" x="50%" font-size="56px" font-family="Arial" dominant-baseline="middle" fill="white" >Subscribe to MNCHAT</text>
"""

svg += "</svg>"

print(svg)
