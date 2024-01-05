

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
            if (isinstance(inp, str) and inp.startswith("#") and inp.lstrip("#").isdigit())
            else None
        )
        return num if isinstance(num, int) and num > 0 else None
    elif isinstance(inp, str):
        inp = inp.lstrip("#")
        return int(inp) if inp.isdigit() and int(inp) > 0 else None
    else:
        return inp if isinstance(inp, int) else None