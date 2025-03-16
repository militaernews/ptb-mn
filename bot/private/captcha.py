import logging
import random
from typing import Final, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont
from telegram import InlineKeyboardButton, Update, InlineKeyboardMarkup, ChatMemberUpdated, ChatMember
from telegram.error import TelegramError
from telegram.ext import CallbackContext, Application, ChatMemberHandler, CallbackQueryHandler

from ..data.lang import GERMAN
from ..settings.config import MSG_REMOVAL_PERIOD

KEYBOARD: Final[str] = "keyboard"

emojis = ['🃏', '🎤', '🎥', '🎨', '🎩', '🎬', '🎭', '🎮', '🎯', '🎱', '🎲', '🎷', '🎸', '🎹', '🎾', '🏀',
          '🏆', '🏈', '🏉', '🏐', '🏓', '💠', '💡', '💣', '💨', '💸', '💻', '💾', '💿', '📈', '📉', '📊',
          '📌', '📍', '📎', '📏', '📐', '📞', '📟', '📠', '📡', '📢', '📣', '📦', '📹', '📺', '📻', '📼',
          '📽', '🖥', '🖨', '🖲', '🗂', '🗃', '🗄', '🗜', '🗝', '🗡', '🚧', '🚨', '🛒', '🛠', '🛢', '🧀', '🌭',
          '🌮', '🌯', '🌺', '🌻', '🌼', '🌽', '🌾', '🌿', '🍊', '🍋', '🍌', '🍍', '🍎', '🍏', '🍚', '🍛',
          '🍜', '🍝', '🍞', '🍟', '🍪', '🍫', '🍬', '🍭', '🍮', '🍯', '🍺', '🍻', '🍼', '🍽', '🍾', '🍿',
          '🎊', '🎋', '🎍', '🎏', '🎚', '🎛', '🎞', '🐌', '🐍', '🐎', '🐚', '🐛', '🐝', '🐞', '🐟', '🐬',
          '🐭', '🐮', '🐯', '🐻', '🐼', '🐿', '👛', '👜', '👝', '👞', '👟', '💊', '💋', '💍', '💎', '🔋',
          '🔌', '🔪', '🔫', '🔬', '🔭', '🔮', '🕯', '🖊', '🖋', '🖌', '🖍', '🥚', '🥛', '🥜', '🥝', '🥞', '🦊',
          '🦋', '🦌', '🦍', '🦎', '🦏', '🌀', '🌂', '🌑', '🌕', '🌡', '🌤', '⛅️', '🌦', '🌧', '🌨', '🌩',
          '🌰', '🌱', '🌲', '🌳', '🌴', '🌵', '🌶', '🌷', '🌸', '🌹', '🍀', '🍁', '🍂', '🍃', '🍄', '🍅',
          '🍆', '🍇', '🍈', '🍉', '🍐', '🍑', '🍒', '🍓', '🍔', '🍕', '🍖', '🍗', '🍘', '🍙', '🍠', '🍡',
          '🍢', '🍣', '🍤', '🍥', '🍦', '🍧', '🍨', '🍩', '🍰', '🍱', '🍲', '🍴', '🍵', '🍶', '🍷', '🍸',
          '🍹', '🎀', '🎁', '🎂', '🎃', '🎄', '🎈', '🎉', '🎒', '🎓', '🎙', '🐀', '🐁', '🐂', '🐃', '🐄',
          '🐅', '🐆', '🐇', '🐕', '🐉', '🐓', '🐖', '🐗', '🐘', '🐙', '🐠', '🐡', '🐢', '🐣', '🐤', '🐥',
          '🐦', '🐧', '🐨', '🐩', '🐰', '🐱', '🐴', '🐵', '🐶', '🐷', '🐸', '🐹', '👑', '👒', '👠', '👡',
          '👢', '💄', '💈', '🔗', '🔥', '🔦', '🔧', '🔨', '🔩', '🔰', '🔱', '🕰', '🕶', '🕹', '🖇', '🚀', '🤖',
          '🥀', '🥁', '🥂', '🥃', '🥐', '🥑', '🥒', '🥓', '🥔', '🥕', '🥖', '🥗', '🥘', '🥙', '🦀', '🦁',
          '🦂', '🦃', '🦄', '🦅', '🦆', '🦇', '🦈', '🦉', '🦐', '🦑', '⭐️', '⏰', '⏲', '⚠️', '⚡️', '⚰️',
          '⚽️', '⚾️', '⛄️', '⛅️', '⛈', '⛏', '⛓', '⌚️', '☎️', '⚜️', '✏️', '⌨️', '☁️', '☃️', '☄️', '☕️',
          '☘️', '☠️', '♨️', '⚒', '⚔️', '⚙️', '✈️', '✉️', '✒️']


def chunked(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def generate_captcha(user_id: int):
    background = Image.open('res/img/captcha.jpg')

    emoji_names = random.sample(emojis, 4)
    paste_image_list = emoji_names.copy()

    width = int(background.width / 3)
    heigth = int(background.height / 2)

    positions = [(width * (i % 2 + 1) - 274 * (i % 2 + 1), heigth * (i // 2 + 1) - 274 * (i // 2 + 1)) for i in
                 range(4)]
    print(positions)

    ImageDraw.Draw(background)
    font = ImageFont.truetype(r"../../res/fonts/AppleColorEmoji.ttf", 137)

    for i, emoji in enumerate(paste_image_list):
        text_layer = Image.new('RGBA', (274, 274), (255, 255, 255, 0))
        draw = ImageDraw.Draw(text_layer)
        draw.text(xy=(0, 0), text=emoji, fill=(255, 255, 255), embedded_color=True, font=font)

        rotated_text_layer = text_layer.rotate(random.randint(0, 350), expand=True, fillcolor=(0, 0, 0, 0))
        background.paste(rotated_text_layer, positions[i], rotated_text_layer)

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
            text = "✅" if btn[1] else btn[0]
            btn_row.append(InlineKeyboardButton(text, callback_data=f"captcha_{x}_{y}"))
        keyboard.append(btn_row)

    return keyboard


def extract_status_change(chat_member_update: ChatMemberUpdated) -> Optional[Tuple[bool, bool]]:
    """Takes a ChatMemberUpdated instance and extracts whether the 'old_chat_member' was a member of the group and
    whether the 'new_chat_member' is a member of the group. Returns None, if the status didn't change.
    """

    status_change = chat_member_update.difference().get("status")
    old_is_member, new_is_member = chat_member_update.difference().get("is_member", (None, None))

    if status_change is None:
        return None

    old_status, new_status = status_change

    was_member = old_status in [ChatMember.MEMBER, ChatMember.OWNER, ChatMember.ADMINISTRATOR, ] or (
            old_status == ChatMember.RESTRICTED and old_is_member is True)

    is_member = new_status in [ChatMember.MEMBER, ChatMember.OWNER, ChatMember.ADMINISTRATOR, ] or (
            new_status == ChatMember.RESTRICTED and new_is_member is True)

    return was_member, is_member


async def send_captcha(update: Update, context: CallbackContext):
    logging.info(f"update :: {update}")
    if update.effective_chat.id != GERMAN.chat_id:
        return

    result = extract_status_change(update.chat_member)
    if result is None:
        return

    logging.info(f"result :: {result}")

    was_member, is_member = result
    cause_name = update.chat_member.from_user.mention_html()
    member_name = update.chat_member.new_chat_member.user.mention_html()

    if not was_member and is_member:
        await update.effective_chat.send_message(f"{member_name} was added by {cause_name}. Welcome!", )
    else:
        return

    answer, captcha = generate_captcha(update.chat_join_request.from_user.id)
    random.shuffle(emojis)

    options = list(answer) + random.sample([em for em in emojis if em not in answer], 8)
    random.shuffle(options)

    state = [[[btn, False] for btn in row] for row in chunked(options, 4)]

    context.user_data["captcha"] = answer
    context.user_data["keyboard"] = state
    logging.info(f"answer: {answer} - keyboard: {state}")

    await context.bot.send_photo(update.chat_join_request.from_user.id, open(captcha, "rb"),
                                 "Bitte löse das Captcha! Klicke dazu alle im Bild befindlichen Emojis an",
                                 reply_markup=InlineKeyboardMarkup(create_keyboard(context)))

    context.job_queue.run_once(decline, MSG_REMOVAL_PERIOD, update.callback_query.from_user.id)


async def click_captcha(update: Update, context: CallbackContext):
    x, y = map(int, update.callback_query.data.split("_")[1:])

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
        try:
            await update.callback_query.delete_message()
            await context.bot.send_message(update.callback_query.from_user.id,
                                           "Vielen Dank für das Lösen des Captchas 😊"
                                           "\n\nBitte warte kurz. Die Admins überprüfen dein Profil.")
        except TelegramError:
            logging.error(f"Failed to delete message from user {update.callback_query.from_user.id}")
    else:
        await update.callback_query.edit_message_reply_markup(InlineKeyboardMarkup(create_keyboard(context)))
        await update.callback_query.answer()


def register_captcha(app: Application):
    app.add_handler(CallbackQueryHandler(click_captcha, r"captcha_.+_.+", ))
    app.add_handler(ChatMemberHandler(send_captcha, ChatMemberHandler.CHAT_MEMBER))
    #  bot.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS & filters.Chat(GERMAN.chat_id), send_captcha))
    #   bot.add_handler(CommandHandler("captcha", send_captcha, filters.Chat(ADMINS)))
