import logging
import time

from telegram import Update
from telegram.ext import CallbackContext

from data.lang import GERMAN


class memo(object):
    """Memoize With Timeout"""
    _caches = {}
    _timeouts = {}

    def __init__(self, timeout=2):
        self.timeout = timeout

    def collect(self):
        """Clear cache of results which have timed out"""
        for func in self._caches:
            cache = {
                key: self._caches[func][key]
                for key in self._caches[func]
                if (time.time() - self._caches[func][key][1])
                   < self._timeouts[func]
            }
            self._caches[func] = cache

    def __call__(self, f):
        self.cache = self._caches[f] = {}
        self._timeouts[f] = self.timeout

        def func(*args, **kwargs):
            kw = sorted(kwargs.items())
            key = (args, tuple(kw))
            try:
                v = self.cache[key]
                print("cache")
                if (time.time() - v[1]) > self.timeout:
                    raise KeyError
            except KeyError:
                print("new")
                v = self.cache[key] = f(*args, **kwargs), time.time()
            return v[0]

        func.func_name = f.__name__

        return func



async def get_admin_ids(context: CallbackContext):
    admins = [admin.user.id for admin in (await context.bot.get_chat_administrators(GERMAN.chat_id))]
    print(admins)
    logging.info(admins)
    return admins
