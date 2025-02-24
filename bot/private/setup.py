import contextlib
import logging
from json import loads
from typing import Dict

from telegram import Update, BotCommandScopeChatAdministrators, BotCommandScopeChat
from telegram.error import BadRequest
from telegram.ext import CallbackContext

from bot.data.lang import LANGUAGES, GERMAN
from bot.settings.config import ADMINS, LOG_GROUP


async def repair_json(update: Update, context: CallbackContext):
    """
    Allow adding entries to saved posts.
    """
    if update.message.caption == "repair":
        await update.message.reply_text("Processing json-file...")

        await repair_saved_post(update, context)


async def repair_saved_post(update: Update, context: CallbackContext):
    filename = await (await update.message.document.get_file()).download_to_drive()

    with open(filename, 'rb') as f:
        content: Dict[str, int] = loads(f.read())
        logging.info(content)

        for key, value in content.items():
            if type(key) is not str or type(value) is not int:
                await update.message.reply_text(
                    "Keys have to be text, values have to be numbers."
                )
                return

        if "de" not in content.keys():
            await update.message.reply_text(f"Missing key \"de\" of the post you want to edit.")
            return

        for lang in LANGUAGES:
            if lang.lang_key not in content.keys():
                await update.message.reply_text(f"Missing key >> {lang.lang_key}")
                return

        post_id = str(content["de"])

        current_dict = None

        if post_id in context.bot_data:
            current_dict = context.bot_data[post_id]
            await update.message.reply_text(f"Entry is present in bot_data. Contents: {current_dict}")

        lang_dict = {
            key: value
            for key, value in content.items()
            if any(lang.lang_key == key for lang in LANGUAGES)
        }
        final_dict = {"langs": lang_dict}

        if "reply" in content:
            final_dict["reply"] = content["reply"]

        await update.message.reply_text(f"Final bot_data: {final_dict}")

        await context.bot.send_message(
           LOG_GROUP,
            f"<b>⚠️ Editing bot_data by user {update.message.from_user.first_name} [<code>{update.message.from_user.id}</code>]</b>\n\n<b>Current bot_data:</b>\n<code>{current_dict}</code>\n\n<b>Input</b>\n<code>{content}</code>\n\n<b>Updated bot_data</b>\n<code>{final_dict}</code>",
        )

        context.bot_data[post_id] = final_dict


async def set_cmd(update: Update, context: CallbackContext):
    await context.bot.delete_my_commands()

    chat_de_commands = [
        ("cmd", "Übersicht aller Befehle"),
        ("maps", "Karten Ukraine-Krieg"),
        ("loss", "Materialverluste in der Ukraine"),
        ("rules", "Regel der Gruppe"),
        ("whitelist", "Erlaubte Links"),
        ("donbas", "14.000 Zivilisten im Donbas"),
        ("stats", "Statistiken"),
        ("short", "Abkürzungen"),
        ("peace", "Russische Kriege"),
        ("bias", "Ist MN neutral?"),
        ("sold", "Söldner Vorrausetzungen"),
        ("genozid", "Kein Genozid der Ukrainer im Donbas"),
        ("sofa", "Waffensystem des Sofa-Kriegers"),
        ("bot", "für Trolle"),
        ("mimimi", "Wenn einer mal wieder heult"),
        ("duden", "Deutsch. Setzen. Sechs."),
        ("argu", "Argumentationspyramide"),
        ("disso", "Kognitive Dissonanz"),
        ("wissen", "Wissen ist Holschuld"),
        ("hominem", "Ad hominem"),
        ("deutsch", "Amtssprache"),
        ("vs", "Verfassungsschutz"),
        ("front", "An die Front!"),
    ]
    await context.bot.set_my_commands(chat_de_commands)

    await context.bot.set_my_commands(chat_de_commands + [
        ("warn", "Nutzer verwarnen"),
        ("unwarn", "Warnung abziehen"),
        ("ban", "Nutzer sperren"),
        ("report", "Tartaros Antispam melden"),
        ("bingo", "Spielfeld des Bullshit-Bingos"),
        ("reset_bingo", "Neue Bingo-Runde")
    ], scope=BotCommandScopeChatAdministrators(GERMAN.chat_id))

    admin_commands = chat_de_commands + [
        ("add_advertisement", "Werbung erstellen"),
    ]
    for chat_id in ADMINS:
        with contextlib.suppress(BadRequest):
            await context.bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=chat_id))
    await update.message.reply_text("Commands updated!")
