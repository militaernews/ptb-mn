import logging
from typing import Dict

from orjson import orjson
from telegram import Update, BotCommandScopeChatAdministrators, BotCommandScopeChat
from telegram.error import BadRequest
from telegram.ext import CallbackContext

import config
import data.lang
from data.lang import languages, GERMAN


async def private_setup(update: Update, context: CallbackContext):
    """
    Allow adding entries to saved posts.
    """
    if update.message.caption == "repair":
        await update.message.reply_text("Processing json-file...")

        await repair_saved_post(update, context)


async def repair_saved_post(update: Update, context: CallbackContext):
    filename = await (await update.message.document.get_file()).download()

    with open(filename, 'rb') as f:
        content: Dict[str, int] = orjson.loads(f.read())
        logging.info(content)

        for key, value in content.items():
            if type(key) is not str or type(value) is not int:
                await update.message.reply_text(f"Keys have to be text, values have to be numbers.")
                return

        if "de" not in content.keys():
            await update.message.reply_text(f"Missing key \"de\" of the post you want to edit.")
            return

        for lang in languages:
            if lang.lang_key not in content.keys():
                await update.message.reply_text(f"Missing key >> {lang.lang_key}")
                return

        post_id = str(content["de"])

        current_dict = None

        if post_id in context.bot_data:
            current_dict = context.bot_data[post_id]
            await update.message.reply_text(f"Entry is present in bot_data. Contents: {current_dict}")

        lang_dict = dict()

        for key, value in content.items():
            if any(lang.lang_key == key for lang in languages):
                lang_dict[key] = value

        final_dict = dict()

        final_dict["langs"] = lang_dict

        if "reply" in content.keys():
            final_dict["reply"] = content["reply"]

        await update.message.reply_text(f"Final bot_data: {final_dict}")

        await context.bot.send_message(
            config.LOG_GROUP,
            f"<b>⚠️ Editing bot_data by user {update.message.from_user.first_name} [<code>{update.message.from_user.id}</code>]</b>\n\n<b>Current bot_data:</b>\n<code>{current_dict}</code>\n\n<b>Input</b>\n<code>{content}</code>\n\n<b>Updated bot_data</b>\n<code>{final_dict}</code>",
        )

        context.bot_data[post_id] = final_dict


async def set_cmd(update: Update, context: CallbackContext):
    await context.bot.delete_my_commands()

    chat_de_commands = [
        ("cmd", "Übersicht aller Befehle"),
        ("maps", "Karten Ukraine-Krieg"),
        ("loss", "Materialverluste in der Ukraine"),
        ("donbas", "14.000 Zivilisten im Donbas"),
        ("stats", "Statistiken"),
        ("short", "Abkürzungen"),
        ("peace", "Russische Kriege"),
        ("bias", "Ist MN neutral?"),
        ("genozid", "Kein Genozid der Ukrainer im Donbas"),
        ("sofa", "Waffensystem des Sofa-Kriegers"),
        ("bot", "für Trolle"),
        ("cia", "Wahrheit über Putin"),
        ("mimimi", "Wenn einer mal wieder heult"),
        ("duden", "Deutsch. Setzen. Sechs."),
    ]
    await context.bot.set_my_commands(chat_de_commands)

    await context.bot.set_my_commands(chat_de_commands + [
        ("warn", "Nutzer verwarnen"),
        ("unwarn", "Warnung abziehen"),
        ("ban", "Nutzer sperren"),
        ("bingo", "Spielfeld des Bullshit-Bingos"),
        ("reset_bingo", "Neue Bingo-Runde")
    ], scope=BotCommandScopeChatAdministrators(GERMAN.chat_id))

    admin_commands = [
        ("add_advertisement", "Werbung erstellen"),
    ]
    for chat_id in config.ADMINS:
        try:
            await context.bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=chat_id))
        except BadRequest:  # to ignore chat not found
            pass

    await update.message.reply_text("Commands updated!")
