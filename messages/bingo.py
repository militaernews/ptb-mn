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
    "böse_NATO",
    "Wunderwaffe",
    "Lindner verspricht",
    "SDF/YPG",
    "Hartz_IV",
    "Atomkrieg",
    "kampferprobt",
    "Spinner",
    "Weltmacht",
    "Kokain",
    "Entnazifizieren",
    "HIMARS",
    "Krim",
    "Russland_droht",
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
    "Putin_macht bald_ernst",
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
    "Kämpf_doch selbst",
    "Propaganda",
    "Taliban",
    "Wahrheit",
    "Aber_die_USA",
    "Ukraine beschießt Zivilisten",
    "Munitionsdepot",
    "Selenski fordert",
    "Man_muss verhandeln",
    "Gas",
    "Bayraktar-TB2",
    "Quelle?",
    "Hostomel",
    "Elite",
    "8_Jahre",
    "Genozid",
    "seit_2014"
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


def create_svg(field: List[List[BingoField]]):
    all_width = 2200
    all_height = 1500

    svg = f"""<?xml version='1.0' encoding='UTF-8' standalone='no'?>
    <svg
       width='{all_width}'
       height='{all_height}'
       viewBox='0 0 {all_width} {all_height}'
       version='1.1'
       xmlns='http://www.w3.org/2000/svg'
       xmlns:svg='http://www.w3.org/2000/svg'>
       <defs>
        <linearGradient id="grad1" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" style="stop-color:#731173;stop-opacity:1" />
          <stop offset="100%" style="stop-color:#400840;stop-opacity:1" />
        </linearGradient>
      </defs>
        <rect x="0" y="0" width="100%" height="100%"  fill="#52237a" />
    <text y="60" x="50%" font-size="56px" font-family="Arial" dominant-baseline="middle"  fill="white" ><tspan dy="0" x="50%" font-weight="bold" text-anchor="middle">Bullshit-Bingo: Runde 0</tspan></text>
    <text y="140" x="50%" font-size="40px" font-family="Arial" dominant-baseline="middle"  fill="white" ><tspan dy="0" x="50%" text-anchor="middle">Wenn eine im MN-Chat gesendete Nachricht auf dem Spielfeld vorkommendende Begriffe enthält, werden diese rausgestrichen.</tspan><tspan dy="1.2em" x="50%" text-anchor="middle">Ist eine gesamte Zeile oder Spalte durchgestrichen, dann heißt es BINGO! 🥳 und eine neue Runde startet.</tspan></text>

    """

    canvas_width = 2020
    canvas_height = 1080
    field_size = 5
    line_width = 6
    height_treshold = int((canvas_height - (field_size * line_width)) / field_size + line_width)
    width_treshold = int((canvas_width - (
            field_size * line_width)) / field_size + line_width)  # int((canvas_size - ((field_size - 1) * line_width)) / field_size + line_width)
    current_width = 0

    svg_field = f"""
    <svg width="{canvas_width}" height="{canvas_height}"  x="{int((all_width - canvas_width) / 2)}" y="240">
    """

    field_counter = 0
    curr_x = 0

    while current_width < canvas_width:
        print(current_width)

        x_var = f"<svg width=\"{width_treshold}\" height=\"{height_treshold}\"  x=\"{current_width}\""
        current_height = 0
        curr_y = 0

        while current_height < canvas_height:
            print(current_height)

            curr_field = field[curr_x][curr_y]
            print(curr_field)

            textss = curr_field.text.split(" ")
            for index, value in enumerate(textss):
                textss[index] = value.replace("_", " ")

            inner_text = """<text  font-size="48px" font-family="Arial" dominant-baseline="middle" """

            if  curr_field.checked:
                inner_text += """text-decoration="line-through" fill="gray" 
                """
            else:
                inner_text += "fill=\"white\" "

            if len(textss) == 1:
                inner_text += f""" dy="50%"><tspan  x="50%" text-anchor="middle">{textss[0]}</tspan>"""
            elif len(textss) == 2:
                inner_text += f""" y="40%" ><tspan  x="50%" text-anchor="middle" dy="1em">{textss[1]}</tspan><tspan  x="50%" text-anchor="middle" dy="-1em">{textss[0]}</tspan>"""
            elif len(textss) == 3:
                inner_text += f"""y="50%"><tspan  x="50%" text-anchor="middle">{textss[1]}</tspan><tspan  x="50%" text-anchor="middle" dy="1em">{textss[2]}</tspan><tspan  x="50%" text-anchor="middle" dy="-2em">{textss[0]}</tspan>"""
            else:
                inner_text = "> TOO LONG"

            svg_field += f"""
            {x_var} y="{current_height}" text-align="center">
           <rect x="0" y="0" width="100%" height="100%"   stroke="#1884cc" stroke-width="6px"  stroke-location="inside" fill="#2a1a3f"  />
           {inner_text}</text>
         </svg>
    """
            curr_y += 1
            current_height += height_treshold
        curr_x += 1
        current_width += width_treshold

    print("lines done, now text -----------------")

    svg_field += "</svg>"

    svg += svg_field

    svg += f"""
    <text y="{all_height - 120}" x="50%" font-size="50px" font-family="Arial" dominant-baseline="middle"  fill="white" ><tspan  x="50%" text-anchor="middle">🔰 Nachrichten rund um Militäraktionen und Proteste - weltweit und brandaktuell 🔰</tspan><tspan dy="1.2em" x="50%" text-anchor="middle">@MNChat @MilitaerNews</tspan></text>
    """

    svg += "</svg>"

    print(svg)

    return svg
