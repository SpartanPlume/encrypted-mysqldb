import logging

logger = logging.getLogger("encrypted_mysqldb")
logger.addHandler(logging.NullHandler())

_crypt = None


def init_crypt(crypt_obj):
    global _crypt
    logger.debug("crypt object set up")
    _crypt = crypt_obj


def get_crypt():
    return _crypt
