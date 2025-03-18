from telegram import Update
from telegram.ext import CallbackContext, CommandHandler, Application

from util.helper import reply_html, reply_photo


async def maps(update: Update, context: CallbackContext):
    await reply_html(update, context, "maps")

    # todo: collect list of losses


async def loss(update: Update, context: CallbackContext):
    await reply_html(update, context, "loss")


async def donbas(update: Update, context: CallbackContext):
    await reply_html(update, context, "donbas")


async def cmd(update: Update, context: CallbackContext):
    await reply_html(update, context, "cmd")


async def genozid(update: Update, context: CallbackContext):
    await reply_html(update, context, "genozid")


async def peace(update: Update, context: CallbackContext):
    await reply_html(update, context, "peace")


async def short(update: Update, context: CallbackContext):
    await reply_html(update, context, "short")


async def stats(update: Update, context: CallbackContext):
    await reply_html(update, context, "stats")


async def bias(update: Update, context: CallbackContext):
    await reply_html(update, context, "bias")


async def sold(update: Update, context: CallbackContext):
    await reply_html(update, context, "sold")


async def osint(update: Update, context: CallbackContext):
    await reply_html(update, context, "osint")


async def sofa(update: Update, context: CallbackContext):
    await reply_photo(update, context, "sofa.jpg")


async def bot(update: Update, context: CallbackContext):
    await reply_photo(update, context, "bot.jpg")


async def mimimi(update: Update, context: CallbackContext):
    await reply_photo(update, context, "mimimi.jpg")


async def duden(update: Update, context: CallbackContext):
    await reply_photo(update, context, "duden.jpg")


async def argu(update: Update, context: CallbackContext):
    await reply_photo(update, context, "argu.jpg")


async def vs(update: Update, context: CallbackContext):
    await reply_photo(update, context, "vs.jpg")


async def disso(update: Update, context: CallbackContext):
    await reply_photo(update, context, "disso.jpg")


async def front(update: Update, context: CallbackContext):
    await reply_photo(update, context, "front.png")


async def deutsch(update: Update, context: CallbackContext):
    await reply_photo(update, context, "deutsch.png")


async def wissen(update: Update, context: CallbackContext):
    await reply_photo(update, context, "wissen.jpg")


async def hominem(update: Update, context: CallbackContext):
    await reply_photo(update, context, "hominem.jpg")


def register_commands(app: Application):
    app.add_handler(CommandHandler("maps", maps))
    app.add_handler(CommandHandler("donbas", donbas))
    app.add_handler(CommandHandler("cmd", cmd))
    app.add_handler(CommandHandler("loss", loss))
    app.add_handler(CommandHandler("peace", peace))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("short", short))
    app.add_handler(CommandHandler("bias", bias))
    app.add_handler(CommandHandler("sold", sold))
    app.add_handler(CommandHandler("osint", osint))
    app.add_handler(CommandHandler("genozid", genozid))

    app.add_handler(CommandHandler("sofa", sofa))
    app.add_handler(CommandHandler("bot", bot))
    app.add_handler(CommandHandler("mimimi", mimimi))
    app.add_handler(CommandHandler("duden", duden))
    app.add_handler(CommandHandler("argu", argu))
    app.add_handler(CommandHandler("vs", vs))
    app.add_handler(CommandHandler("disso", disso))
    app.add_handler(CommandHandler("front", front))
    app.add_handler(CommandHandler("deutsch", deutsch))
    app.add_handler(CommandHandler("wissen", wissen))
    app.add_handler(CommandHandler("hominem", hominem))
