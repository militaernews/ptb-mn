import logging
import random
from random import randint
from typing import Final

from PIL import Image, ImageDraw, ImageFont
from telegram import InlineKeyboardButton, Update, InlineKeyboardMarkup
from telegram.ext import CallbackContext

import config

from data.lang import GERMAN
from util.helper import MSG_REMOVAL_PERIOD

KEYBOARD: Final[str] = "keyboard"

supported_emojis = ['🃏', '🎤', '🎥', '🎨', '🎩', '🎬', '🎭', '🎮', '🎯', '🎱', '🎲', '🎷', '🎸', '🎹', '🎾', '🏀', '🏆', '🏈', '🏉',
                    '🏐',
                    '🏓', '💠', '💡', '💣', '💨', '💸', '💻', '💾', '💿', '📈', '📉', '📊', '📌', '📍', '📎', '📏', '📐', '📞', '📟',
                    '📠',
                    '📡', '📢', '📣', '📦', '📹', '📺', '📻', '📼', '📽', '🖥', '🖨', '🖲', '🗂', '🗃', '🗄', '🗜', '🗝', '🗡', '🚧',
                    '🚨',
                    '🛒', '🛠', '🛢', '🧀', '🌭', '🌮', '🌯', '🌺', '🌻', '🌼', '🌽', '🌾', '🌿', '🍊', '🍋', '🍌', '🍍', '🍎', '🍏',
                    '🍚',
                    '🍛', '🍜', '🍝', '🍞', '🍟', '🍪', '🍫', '🍬', '🍭', '🍮', '🍯', '🍺', '🍻', '🍼', '🍽', '🍾', '🍿', '🎊', '🎋',
                    '🎍',
                    '🎏', '🎚', '🎛', '🎞', '🐌', '🐍', '🐎', '🐚', '🐛', '🐝', '🐞', '🐟', '🐬', '🐭', '🐮', '🐯', '🐻', '🐼', '🐿',
                    '👛',
                    '👜', '👝', '👞', '👟', '💊', '💋', '💍', '💎', '🔋', '🔌', '🔪', '🔫', '🔬', '🔭', '🔮', '🕯', '🖊', '🖋', '🖌',
                    '🖍',
                    '🥚', '🥛', '🥜', '🥝', '🥞', '🦊', '🦋', '🦌', '🦍', '🦎', '🦏', '🌀', '🌂', '🌑', '🌕', '🌡', '🌤', '⛅️', '🌦',
                    '🌧',
                    '🌨', '🌩', '🌰', '🌱', '🌲', '🌳', '🌴', '🌵', '🌶', '🌷', '🌸', '🌹', '🍀', '🍁', '🍂', '🍃', '🍄', '🍅', '🍆',
                    '🍇',
                    '🍈', '🍉', '🍐', '🍑', '🍒', '🍓', '🍔', '🍕', '🍖', '🍗', '🍘', '🍙', '🍠', '🍡', '🍢', '🍣', '🍤', '🍥', '🍦',
                    '🍧',
                    '🍨', '🍩', '🍰', '🍱', '🍲', '🍴', '🍵', '🍶', '🍷', '🍸', '🍹', '🎀', '🎁', '🎂', '🎃', '🎄', '🎈', '🎉', '🎒',
                    '🎓',
                    '🎙', '🐀', '🐁', '🐂', '🐃', '🐄', '🐅', '🐆', '🐇', '🐕', '🐉', '🐓', '🐖', '🐗', '🐘', '🐙', '🐠', '🐡', '🐢',
                    '🐣',
                    '🐤', '🐥', '🐦', '🐧', '🐨', '🐩', '🐰', '🐱', '🐴', '🐵', '🐶', '🐷', '🐸', '🐹', '👑', '👒', '👠',
                    '👡', '👢', '💄', '💈', '🔗', '🔥', '🔦', '🔧', '🔨', '🔩', '🔰', '🔱', '🕰', '🕶', '🕹', '🖇', '🚀', '🤖', '🥀',
                    '🥁',
                    '🥂', '🥃', '🥐', '🥑', '🥒', '🥓', '🥔', '🥕', '🥖', '🥗', '🥘', '🥙', '🦀', '🦁', '🦂', '🦃', '🦄', '🦅', '🦆',
                    '🦇',
                    '🦈', '🦉', '🦐', '🦑', '⭐️', '⏰', '⏲', '⚠️', '⚡️', '⚰️', '⚽️', '⚾️', '⛄️', '⛅️', '⛈', '⛏', '⛓',
                    '⌚️',
                    '☎️', '⚜️', '✏️', '⌨️', '☁️', '☃️', '☄️', '☕️', '☘️', '☠️', '♨️', '⚒', '⚔️', '⚙️', '✈️', '✉️',
                    '✒️']


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def generate_captcha(user_id: int):
    background = Image.open(f'res/img/captcha.jpg', )
    paste_image_list = list()
    emoji_names = list()

    random.shuffle(supported_emojis)

    for i in range(4):
        emoji_names.append(supported_emojis[i])
        paste_image_list.append(supported_emojis[i])

    width = int(background.width / 3)
    heigth = int(background.height / 2)

    position = [(width * 1 - 274 * 1, heigth * 1 - 274 * 1), (int(width * 3.4 - 274 * 3), heigth * 1 - 274 * 1),
                (width * 1 - 274 * 1, heigth * 2 - 274 * 2), (width * 2 - 274 * 2, int(heigth * 2.2 - 274 * 2))]
    print(position)

    draw = ImageDraw.Draw(background)
    font = ImageFont.truetype(r"AppleColorEmoji.ttf", 137)

    for i, emoji in enumerate(paste_image_list):
        text_layer = Image.new('RGBA', (274, 274), (255, 255, 255, 0))
        draw = ImageDraw.Draw(text_layer)
        draw.text(xy=(0, 0), text=emoji, fill=(255, 255, 255), embedded_color=True, font=font)

        rotated_text_layer = text_layer.rotate(random.randint(0, 350),
                                               expand=True, fillcolor=(0, 0, 0, 0), resample=Image.BICUBIC)
        background.paste(rotated_text_layer, position[i], rotated_text_layer)

    emoji_captcha_path = f"temp/captcha_{user_id}.png"

    background.save(emoji_captcha_path, "PNG", quality=100)
    res = emoji_names, emoji_captcha_path

    print(res)
    return res


async def decline(context: CallbackContext):
    await context.bot.decline_chat_join_request(GERMAN.chat_id, int(context.job.data))


def create_keyboard(context: CallbackContext):
    keyboard = []
    for x, row in enumerate(context.user_data["keyboard"]):
        btn_row = []
        for y, btn in enumerate(row):
            if btn[1]:
                text = "✅"
            else:
                text = btn[0]

            btn_row.append(InlineKeyboardButton(text, callback_data=f"captcha_{x}_{y}"))
        keyboard.append(btn_row)

    return keyboard


async def send_captcha(update: Update, context: CallbackContext):
    answer, captcha = generate_captcha(update.chat_join_request.from_user.id)
    random.shuffle(supported_emojis)

    options = list(answer)
    for em in supported_emojis:
        if len(options) == 12:
            break
        if em not in options:
            options.append(em)
    random.shuffle(options)

    state = []
    for row in chunks(options, 4):
        state_row = []
        for btn in row:
            state_row.append([btn, False])
        state.append(state_row)

    context.user_data["captcha"] = answer
    context.user_data["keyboard"] = state
    logging.info(f"answer: {answer} - keyboard: {state}")

    await context.bot.send_photo(update.chat_join_request.from_user.id, open(captcha, "rb"),
                                 "Bitte löse das Captcha! Klicke dazu alle im Bild befindlichen Emojis an",
                                 reply_markup=InlineKeyboardMarkup(create_keyboard(context)))

    context.job_queue.run_once(decline, MSG_REMOVAL_PERIOD, update.callback_query.from_user.id)


async def click_captcha(update: Update, context: CallbackContext):
    x, y = update.callback_query.data.split("_")[1:]
    x = int(x)
    y = int(y)

    context.user_data[KEYBOARD][x][y][1] = not context.user_data[KEYBOARD][x][y][1]

    active = 0
    correct = 0
    for row in context.user_data[KEYBOARD]:
        for btn in row:
            if btn[1]:
                active += 1
                if btn[0] in context.user_data["captcha"]:
                    correct += 1

    logging.info(f"{update.callback_query.from_user.id} - correct: {correct} - active: {active}")
    if correct == 4 and active == 4:
        await update.callback_query.message.delete()
        await context.bot.send_message(update.callback_query.from_user.id,
                                       "Vielen Dank für das Lösen des Captchas 😊"
                                       "\n\nBitte warte kurz. Die Admins überprüfen dein Profil.")

    else:
        await update.callback_query.edit_message_reply_markup(InlineKeyboardMarkup(create_keyboard(context)))
        await update.callback_query.answer()