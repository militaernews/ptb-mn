import datetime
import random
from dataclasses import dataclass
from typing import List

import cairosvg
import numpy as numpy
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import CallbackContext

from data.lang import GERMAN

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


field_size = 5


def generate_bingo_field():
    random.shuffle(ENTRIES)

    outer = list()

    for x in range(1, field_size * field_size, field_size):
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


def set_checked(text: str, fields: List[List[BingoField]]):
    found = False
    print(list(numpy.array(fields).flat))
    for item in list(numpy.array(fields).flat):
        if item.text.replace("_", " ").lower() in text.lower():
            item.checked = True
            found = True
            print(f"{text} is a valid bingo entry")

    return found


def create_svg(field: List[List[BingoField]]):
    all_width = 2460
    all_height = 1460

    canvas_width = 2360
    canvas_height = 1200
    border_distance = int((all_width - canvas_width) / 2)
    print("border_distance", border_distance)

    svg = f"""<?xml version='1.0' encoding='UTF-8' standalone='no'?>
    <svg
       width='{all_width}'
       height='{all_height}'
       viewBox='0 0 {all_width} {all_height}'
       version='1.1'
       xmlns='http://www.w3.org/2000/svg'
       xmlns:svg='http://www.w3.org/2000/svg'>
      
    <text y="{border_distance + 60}" x="50%" font-size="60px" font-family="Arial" dominant-baseline="middle"  fill="white" ><tspan dy="0" x="50%" font-weight="bold" text-anchor="middle">Militär-News Bullshit-Bingo</tspan></text>
    """

    line_width = 2
    line_half = int(line_width / 2)
    height_treshold = int((canvas_height - (field_size * line_width)) / field_size + line_width)
    width_treshold = int((canvas_width - (
            field_size * line_width)) / field_size + line_width)
    current_width = 0

    svg_field = f"""
    <svg width="{canvas_width}" height="{canvas_height}"  x="{border_distance - line_half}" y="170"    viewBox='{-line_half} {-line_half} {canvas_width + line_half} {canvas_height + line_half}'>
    """

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

            inner_text = """<text  font-size="48px" font-family="Arial" dominant-baseline="central" """

            if curr_field.checked:
                inner_text += "fill=\"#e8cc00\" "
            else:
                inner_text += "fill=\"white\" "

            if len(textss) == 1:
                inner_text += f""" y="50%"><tspan  x="50%" text-anchor="middle">{textss[0]}</tspan>"""
            elif len(textss) == 2:
                inner_text += f""" y="40%" ><tspan  x="50%" text-anchor="middle" dy="1em">{textss[1]}</tspan><tspan  x="50%" text-anchor="middle" dy="-1em">{textss[0]}</tspan>"""
            elif len(textss) == 3:
                inner_text += f"""y="50%"><tspan  x="50%" text-anchor="middle">{textss[1]}</tspan><tspan  x="50%" text-anchor="middle" dy="1em">{textss[2]}</tspan><tspan  x="50%" text-anchor="middle" dy="-2em">{textss[0]}</tspan>"""
            else:
                inner_text = "> TOO LONG"

            svg_field += f"""
            {x_var} y="{current_height}" text-align="center">
           <rect x="0" y="0" width="100%" height="100%"   stroke="#2c5a2b" stroke-width="6px" paint-order="fill" fill="#002a24"  />
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
    <text y="{all_height - border_distance}" x="{all_width - border_distance}" font-size="26px" font-family="Arial" dominant-baseline="middle"  text-anchor="end" fill="gray" >zuletzt aktualisiert {datetime.datetime.now().strftime("%d.%m.%Y, %H:%M:%S")}</text>
    </svg>"""

    print(svg)

    cairosvg.svg2png(bytestring=svg, write_to='field.png', background_color="#00231e")


async def filter_message(update: Update, context: CallbackContext):
    text = update.message.text.lower()

    if 1 == 2:
        print("Spam detected")
    # todo: filter and report

    elif datetime.datetime.now().weekday() == 6:  # Sunday
        print("checking bingo...")
        if "bingo" not in context.bot_data:
            context.bot_data["bingo"] = generate_bingo_field()
            create_svg(context.bot_data["bingo"])

        if set_checked(text, context.bot_data["bingo"]) and check_win(context.bot_data["bingo"]):
            create_svg(context.bot_data["bingo"])
            with open("field.png", "rb") as f:
                await update.message.reply_photo(photo=f,
                                                 caption=f"<b>BINGO! 🥳</b>\n\n {update.message.from_user.name} hat den letzten Begriff beigetragen. So sah das Spielfeld am Ende aus.\n\nEine neue Runde beginnt...\n{GERMAN.footer}")
            context.bot_data["bingo"] = generate_bingo_field()


async def bingo_field(update: Update, context: CallbackContext):
    try:
        create_svg(context.bot_data["bingo"])
        with open("field.png", "rb") as f:
            await update.message.reply_photo(photo=f,
                                             caption=f"<b>Militär-News Bullshit-Bingo</b>\n\nWenn eine im @MNChat gesendete Nachricht auf dem Spielfeld vorkommendende Begriffe enthält, werden diese rausgestrichen.\n\nIst eine gesamte Zeile oder Spalte durchgestrichen, dann heißt es <b>BINGO!</b> und eine neue Runde startet.\n{GERMAN.footer}")
    except FileNotFoundError as e:
        print("No field yet")
