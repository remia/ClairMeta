# Clairmeta - (C) YMAGIS S.A.
# See LICENSE for more information


class ClairMetaException(Exception):
    """Base class for all exception raised by this library."""


class CommandException(ClairMetaException):
    """Raised when external command fails."""


class ProbeException(ClairMetaException):
    """Raised when probing a DCP fails."""

    def __init__(self, msg):
        super().__init__(str(msg))


class CheckException(ClairMetaException):
    """Non recoverable errors while checking a DCP.

    This is not to be used for regular check errors, where we instead use
    ``error()`` and ``fatal_error()`` methods.

    """
