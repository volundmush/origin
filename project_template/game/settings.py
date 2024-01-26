from origin.settings_default import *


# Add to/override/create new settings in your profile below!


# And then don't forget the secret settings...
try:
    from .secret_settings import *
except ImportError:
    pass
