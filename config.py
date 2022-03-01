"""Contains variables used throughout the project."""
import os

PORT = int(os.environ.get("PORT", 5000))
TOKEN = os.environ["TOKEN"]

CHANNEL_MEME = -1001486678205

GROUP_MAIN = -1001526741474

NYX = 703453307
ADMINS = (NYX, 806473770, 1971709534)  # BlueBettle  # Phoenix
VERIFIED_USERS = set(
    ADMINS + (924295169, 1038099761, 1128670209)  # Lucky  # Abhiskek  # LalitSaini
)
