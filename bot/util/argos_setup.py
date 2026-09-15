"""Installs the Argos Translate language packages used as an offline
translation fallback when Google Translate is unavailable.

German is the only source language posts are written in, and Argos only
ships a direct de->en model. Every other target language is reached by
Argos pivoting through English automatically once both the de->en package
and the relevant en->target package are installed - so both hops must be
present for a language to work.

Deliberately has no imports from the rest of the bot package so it can run
standalone (e.g. baked into the Docker image at build time, before the
bot's own settings/config are relevant).
"""

import logging

import argostranslate.package

ARGOS_TARGET_LANGUAGES = ("en", "tr", "fa", "ru", "pt", "es", "fr", "it", "ar", "id")
ARGOS_PACKAGES = [("de", "en")] + [("en", target) for target in ARGOS_TARGET_LANGUAGES if target != "en"]


def install_argos_models() -> None:
    installed = {(p.from_code, p.to_code) for p in argostranslate.package.get_installed_packages()}
    missing = [pair for pair in ARGOS_PACKAGES if pair not in installed]

    if not missing:
        logging.info("Argos Translate: all required language packages already installed")
        return

    argostranslate.package.update_package_index()

    for from_code, to_code in missing:
        try:
            if argostranslate.package.install_package_for_language_pair(from_code, to_code):
                logging.info(f"Argos Translate: installed {from_code}->{to_code}")
            else:
                logging.error(f"Argos Translate: no package available for {from_code}->{to_code}")
        except Exception as e:
            logging.error(f"Argos Translate: failed to install {from_code}->{to_code}: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    install_argos_models()
