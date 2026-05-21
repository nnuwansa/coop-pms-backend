class NoDataFoundException(Exception):
    def __init__(self, message: str):
        self.message = message


class CodeExistException(Exception):
    def __init__(self, message: str):
        self.message = message


class LetterNotFoundException(Exception):
    def __init__(self, message: str):
        self.message = message


class FileTooLargeException(Exception):
    def __init__(self, message: str):
        self.message = message


class UnsupportedFileTypeException(Exception):
    def __init__(self, message: str):
        self.message = message


class FileDeletionException(Exception):
    def __init__(self, message: str):
        self.message = message


class DuplicateEntryException(Exception):
    def __init__(self, message: str):
        self.message = message


class UnauthorizedException(Exception):
    def __init__(self, message: str):
        self.message = message


class UnRefreshingException(Exception):
    def __init__(self, message: str):
        self.message = message
