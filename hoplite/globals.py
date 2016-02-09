"""
Modules for classes that are used as containers for global variables.
Any function can import and modify/read the values stored in these classes.
"""


class HopliteServerSettings():
    """
    Holds global hoplite settings for the server.
    """
    # Debug mode increases the amount of logging performed by certain
    # functions.
    debug = False


class HopliteClientSettings():
    """
    Holds global hoplite settings for the client.
    """
    # Debug mode increases the amount of logging performed by certain
    # functions.
    debug = False
