# Note - only certain exceptions can be pickled and unpickled. Specifically,
# custom exceptions with arguments to the __init__ function must be written
# with all arguments as optional, as shown below.


class ExternalCustomError(Exception):
    def __init__(self, msg=None):
        self.message = msg


class ExternalEmptyError(Exception):
    pass