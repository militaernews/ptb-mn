import datetime
import random
import re
from typing import List, Union, Dict

import cairosvg
import numpy as numpy
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import CallbackContext
from telegram.helpers import mention_html

from data.lang import GERMAN

load_dotenv()

ENTRIES = {
    "Israel": None,
    "Baerbock verurteilt": None,
    "Lauterbach warnt": None,
    "China": None,
    "wirkungsvoll": None,
    "Biden": None,
    "Schwurbler": None,
    "Schneelensky": None,
    "Booster": None,
    "Zwang": None,
    # "Genozid",
    # "Völkermord",
    "Dampfplauderer": None,
    "Drogen": None,
    "geimpft": None,
    "böse_NATO": None,
    "Wunderwaffe": None,
    "Offensive": None,
    "Lindner verspricht": None,
    "SDF/YPG": None,
    "Hartz_IV": None,
    "Atomkrieg": None,
    "kampferprobt": None,
    "Spinner": None,
    "Weltmacht": None,
    "Kokain": None,
    "Entnazifizierung": r"Entnazifizieren|Entnazifizierung",
    "HIMARS": None,
    "Krim": None,
    "Russland_droht": None,
    "Biolabor": None,
    "Schlangeninsel": None,
    "Faschist": None,
    "Nazi": None,
    "Britischer Geheimdienst": r"Britische(r*) Geheimdienst",
    "Azov": r"A(s|z)o[w|v)",
    "Alina Lipp": "Alina|Lipp",
    "Erdogan": None,
    "Korruption": None,
    "Konvention": None,
    "Lufthoheit": None,
    "Taiwan": None,
    "Frontverlauf": None,
    "Kinzhal": None,
    "Meinung": None,
    "Lukashenko": "Lukas(c*)henko",
    "Impfung": r"Impfung|impfen|geimpft",
    "Reichsbürger": None,
    "Trump": None,
    "Schwarzmarkt": None,
    "Troll": None,
    "WEF": None,
    "Bill Gates": None,
    "Dimension": None,
    "Reptiloid": None,
    "Gerücht": None,
    "System": None,
    "einsatzbereit": None,
    "Putin_macht bald_ernst": None,
    "Militärexperte": None,
    "Zweiter Weltkrieg": r"Zweite(r|n) Weltkrieg|WW2|WK",
    "Palästina": None,
    "Verluste": None,
    "Logistik": None,
    "Stalingrad": None,
    "Barbarossa": None,
    "Wehrmacht": None,
    "Unfall": None,
    "Raucher": None,
    "Ivan": None,
    "Osterweiterung": None,
    "Vorstoß": None,
    "T-14 Armata": "T(-*)14|Armata",
    "Kämpf_doch selbst": None,
    "Propaganda": None,
    "Taliban": None,
    "Wahrheit": None,
    "Aber_die_USA": None,
    "Ukraine beschießt Zivilisten": None,
    "Munitionsdepot": None,
    "Selenski fordert": None,
    "Man_muss verhandeln": None,
    "Gas": None,
    "Bayraktar TB2": r"Bayraktar|Baykar|TB2|TB-2",
    "Quelle?": None,
    "Hostomel": None,
    "Elite": None,
    "8_Jahre": None,
    "Genozid": None,
    "seit_2014": None,
    "Hohol": None,
    "Irpin": None,
    "Butscha": None,
    "Klitschko": None,
    "Chornobayivka": None,
    "Lipp": None,
    "Ork": None,
    "Belgorod": None,
    "kapitulieren": None,
    "aufgeben": None,
    "Vakuumbombe": None,
    "thermobarisch": None,
    "Sanktion": None,
    "Deflation": None,
    "Wagner": None,
    "Volksrepublik": None,
    "Referendum": None,
    "russophob": None,
    "Eskalation": None,
    "AKW": None,
    "Gaspreis": None,
    "reagiert": None,
    "Globohomo": None,
    "Doppelmoral": None,
    "Euromaidan": None,
    "Clown": None,
    "9/11": None,
    "Rothschild": None,
    "Ukronazi": None,
    "Beischlafbettler": None
}

field_size = 5


def generate_bingo_field():
    key_list = list(ENTRIES)

    random.shuffle(key_list)

    d2 = {}

    for key in key_list:
        print(key, ENTRIES[key])
        d2[key] = ENTRIES[key]

    outer = list()

    for x in range(1, field_size * field_size, field_size):
        inner = list()
        print(x)

        for entry in list(d2.items())[x:x + field_size]:
            print("ENTRY >>>>>>>>> ", entry, entry[0])
            if entry[1] is None:
                regex = entry[0]
            else:
                regex = entry[1]

            inner.append({
                "text": entry[0],
                "checked": False,
                "regex": regex
            })

        outer.append(inner)

    print(outer)
    return outer


def check_win(fields: List[List[Dict[str, Union[str, bool]]]]):
    # horizontal condition
    for row in fields:
        if all(item["checked"] for item in row):
            return True

    # vertical condition
    for column in zip(*fields):
        if all(item["checked"] for item in column):
            return True

    return False


def set_checked(text: str, fields: List[List[Dict[str, Union[str, bool]]]]):
    found = list()
    print(list(numpy.array(fields).flat))
    for item in list(numpy.array(fields).flat):
        if not item["checked"] and re.match(item["regex"], text, re.IGNORECASE) is not None:
            item["checked"] = True
            found.append(item["text"])
            print(f"{text} is a valid bingo entry")

    return found


def create_svg(field: List[List[Dict[str, Union[str, bool]]]]):
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

            textss = curr_field["text"].split(" ")
            for index, value in enumerate(textss):
                textss[index] = value.replace("_", " ")

            inner_text = """<text  font-size="48px" font-family="Arial" dominant-baseline="central" """

            if curr_field["checked"]:
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


async def handle_bingo(update: Update, context: CallbackContext):
    text = update.message.text.lower()

    # elif datetime.datetime.now().weekday() == 5 or datetime.datetime.now().weekday() == 6:
    print("checking bingo...")
    if "bingo" not in context.bot_data:
        context.bot_data["bingo"] = generate_bingo_field()
        create_svg(context.bot_data["bingo"])

    found = set_checked(text, context.bot_data["bingo"])
    found_amount = len(found)

    if found_amount != 0:

        if check_win(context.bot_data["bingo"]):
            create_svg(context.bot_data["bingo"])
            with open("field.png", "rb") as f:
                msg = await  update.message.reply_photo(photo=f,
                                                        caption=f"<b>BINGO! 🥳</b>\n\n{mention_html(update.message.from_user.id, update.message.from_user.first_name)} hat den letzten Begriff beigetragen. Die erratenen Begriffe sind gelb eingefärbt.\n\nEine neue Runde beginnt...\n{GERMAN.footer}")
                await msg.pin()
            context.bot_data["bingo"] = generate_bingo_field()
        else:

            text = '<b>Treffer! 🥳</b>\n\n'

            for index, word in enumerate(found):
                text += f'\"{word}\"'

                if index == found_amount - 1:
                    if found_amount == 1:
                        text += " ist ein gesuchter Begriff"
                    else:
                        text += " sind gesuchte Begriffe"

                    text += " im Bullshit-Bingo."

                elif index == found_amount - 2:
                    text += " und "

                else:
                    text += ", "

            await update.message.reply_text(text)


async def bingo_field(update: Update, context: CallbackContext):
    try:
        if "bingo" not in context.bot_data:
            context.bot_data["bingo"] = generate_bingo_field()
        create_svg(context.bot_data["bingo"])
        with open("field.png", "rb") as f:
            await update.message.reply_photo(photo=f,
                                             caption=f"<b>Militär-News Bullshit-Bingo</b>\n\nWenn eine im @MNChat gesendete Nachricht auf dem Spielfeld vorkommendende Begriffe enthält, werden diese rausgestrichen.\n\nIst eine gesamte Zeile oder Spalte durchgestrichen, dann heißt es <b>BINGO!</b> und eine neue Runde startet.\n{GERMAN.footer}")
    except FileNotFoundError as e:
        print("No field yet")


async def reset_bingo(update: Update, context: CallbackContext):
    context.bot_data["bingo"] = generate_bingo_field()
    await update.message.reply_text(f"Bingo was reset!\n\n{context.bot_data['bingo']}")
