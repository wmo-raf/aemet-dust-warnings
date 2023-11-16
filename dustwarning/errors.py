class Error(Exception):

    def __init__(self, message):
        self.message = message

    @property
    def serialize(self):
        return {
            'message': self.message
        }


class WarningsNotFound(Error):
    pass


class WarningsRequestError(Error):
    pass


class IncompleteWarningsFetch(Error):
    pass
