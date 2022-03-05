"""Contains variables used throughout the project."""
import os

PORT = int(os.environ.get("PORT", 5000))
TOKEN = os.environ["TOKEN"]

CHANNEL_MEME = -1001486678205
CHANNEL_DE = -1001240262412
CHANNEL_EN = -1001258430463

GROUP_MAIN = -1001526741474

NYX = 703453307
ADMINS = (NYX,
          525147382,  # melik
          466451473  # maxe
          )
VERIFIED_USERS = set(
    ADMINS + ()
)
