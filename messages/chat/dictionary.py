from telegram import Update
from telegram.ext import CallbackContext

putin_dict = {
    "️Angriff": "erzwungene Selbstverteidigung",
    "️Arrest": "Einladung zu einem Vorstellungsgespräch",
    "️Flüchtlinge": "Neonazis und Drogenabhängige",
    "️Arbeitslose": "Arbeitsferien",
    "️Bombardierungen": "Entmilitarisierung",
    "️Schlachten": "Bohrer",
    "Verluste": "Fälschungen",
    "️Kriegsführung": "Sondereinsätze",
    "️Bombardierung": "klatschen",
    "️Invasion": "Entmilitarisierung",
    "️Ausfall": "wirtschaftliche Umstrukturierung",
    "️Verhör": "Befragung",
    "️Diktatur": "Demokratie",
    "️Beschäftigung": "Befreiung",
    "️Neubehandlung": "Umgruppierung",
    "️Rückgang": "negatives Wachstum",
    "️Folter": "Vorbereitung auf ein Vorstellungsgespräch",
    "️Entzug": "wirtschaftliche Optimierung",
    "️Sanktion": "Stärkung der eigenen Wirtschaft",
    "️Zensur": "Meinungsfreiheit",
    "️Wirtschaftssanktionen": "Importsubstitution",
    "️Faschismus": "Entnazifizierung",
    "️Mobilisiert": "Russische Eliteeinheit",
    "️Waschmaschine": "Chip-Spender",
    "Trauer": "mysteriöser Todesfall",
    "️Absturz": "schnelle taktische Landungsoperation",
    "️Krieg": "dreitägige Spezialoperation",
    "️Agent": "kritischer Journalist",
    "️Journalist": "feindlicher Spion",
    "️Wohnhaus": "militärische Stellung",
    "Schule": "Nazi-Hauptquartier",
    "Flucht": "Umgruppierung in eine strategisch bessere Position",
    "Zwangsrekrutierte": "Freiwillige",
    "Rückzug": "negativer Gebietsgewinn",
    "Friendlyfire": "Frühjahrsputz",
    "Putintroll": "braver Mitbürger",
    "Putler": "Zar Vladimir der Einzige",
    "Hilfsgüter": "ukrainische Kokaintransporte"
}


async def handle_putin_dict(update: Update, context: CallbackContext):
    matches = {}

    for k, v in putin_dict.items():

     #   print(k, update.message.text, k in update.message.text, " LLLLLLLLLLLLLLLLLLLLL")

    #    print(k, " --- IN --- ", v)
        if k.lower() in update.message.text.lower():  # and k not in matches.keys():
            print("---------- MATCH ----------")
            matches[k] = v

    print(update.message.text, "-------", matches, putin_dict)

    if len(matches) == 0:
        return

    text = f"☝🏼 Laut der neuen putin'schen Rechtschreibung hast du hier ein paar Fehler gemacht:"

    for k, v in matches.items():
        text += f"\n\n❗️ „{k}” muss „{v}” lauten!"

    await update.message.reply_text(text)
