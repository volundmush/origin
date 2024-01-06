import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email as django_validate_email
import mudforge
from mudforge.utils import to_str


def dbref(inp, reqhash=True):
    """
    Converts/checks if input is a valid dbref.

    Args:
        inp (int, str): A database ref on the form N or #N.
        reqhash (bool, optional): Require the #N form to accept
            input as a valid dbref.

    Returns:
        dbref (int or None): The integer part of the dbref or `None`
            if input was not a valid dbref.

    """
    if reqhash:
        num = (
            int(inp.lstrip("#"))
            if (
                isinstance(inp, str)
                and inp.startswith("#")
                and inp.lstrip("#").isdigit()
            )
            else None
        )
        return num if isinstance(num, int) and num > 0 else None
    elif isinstance(inp, str):
        inp = inp.lstrip("#")
        return int(inp) if inp.isdigit() and int(inp) > 0 else None
    else:
        return inp if isinstance(inp, int) else None


def validate_email_address(emailaddress):
    """
    Checks if an email address is syntactically correct. Makes use
    of the django email-validator for consistency.

    Args:
        emailaddress (str): Email address to validate.

    Returns:
        bool: If this is a valid email or not.

    """
    try:
        django_validate_email(str(emailaddress))
    except DjangoValidationError:
        return False
    except Exception:
        logging.exception(f"Error while validating email.")
        return False
    else:
        return True


def crop(text, width=None, suffix="[...]"):
    """
    Crop text to a certain width, throwing away text from too-long
    lines.

    Args:
        text (str): Text to crop.
        width (int, optional): Width of line to crop, in characters.
        suffix (str, optional): This is appended to the end of cropped
            lines to show that the line actually continues. Cropping
            will be done so that the suffix will also fit within the
            given width. If width is too small to fit both crop and
            suffix, the suffix will be dropped.

    Returns:
        text (str): The cropped text.

    """
    width = width if width else mudforge.GAME.settings.CLIENT_DEFAULT_WIDTH
    ltext = len(text)
    if ltext <= width:
        return text
    else:
        lsuffix = len(suffix)
        text = (
            text[:width]
            if lsuffix >= width
            else "%s%s" % (text[: width - lsuffix], suffix)
        )
        return to_str(text)


class SessionHandler:
    def __init__(self, obj):
        self.obj = obj
        self.sessions = set()

    def add(self, sess):
        self.sessions.add(sess)

    def remove(self, sess):
        self.sessions.remove(sess)

    def all(self):
        return set(self.sessions)

    def count(self):
        return len(self.sessions)
