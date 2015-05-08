"""
# ----------------------------------------------------------------------
# error.py
#
# Error logging and reporting module. Utilizes python logging.
#
# Author: Nick Korasidis <Renelvon@gmail.com>
# ----------------------------------------------------------------------
"""

import logging


class LoggerInterface:

    """
    Interface and minimal implementation of a logger.

    Mainly used for testing purposes.
    """

    def __init__(self):
        self.clear()

    def clear(self):
        """Reset logger state for testability"""
        self.errors = 0
        self.warnings = 0

    def debug(self, fmt, *args):
        return

    def info(self, fmt, *args):
        return

    def warning(self, fmt, *args):
        self.warnings += 1

    def error(self, fmt, *args):
        self.errors += 1

    @property
    def success(self):
        """Operation is successful iff zero errors are logged."""
        return self.errors == 0

    @property
    def perfect_success(self):
        """
        Operation is perfectly successful iff zero errors/warnings
        are logged.
        """
        return self.errors == 0 and self.warnings == 0


class LoggerMock(LoggerInterface):

    """Mock of a full logger. Mainly used for testing purposes."""

    pass


class Logger(LoggerInterface):

    """
    Simple error logger for the llama compiler.

    Provides methods for logging and reporting errors of varying
    severities. It is intended that all modules share one instance of
    this class.
    """

    # Number of Logger instances created
    _instances = 0

    # The logger instance, as constructed by the logging module
    _logger = None

    def __init__(self, inputfile="<stdin>", level=logging.WARNING):
        """Create a new logger for the llama compiler."""
        super().__init__()

        self._logger = logging.getLogger('llama%d' % Logger._instances)
        Logger._instances += 1
        self._logger.setLevel(level)
        formatter = logging.Formatter(inputfile + ": %(message)s")
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)

    def error(self, fmt, *args):
        """Add an error to the logger."""
        self._logger.error(fmt, *args)
        self.errors += 1

    def warning(self, fmt, *args):
        """Add a warning to the logger."""
        self._logger.warning(fmt, *args)
        self.warnings += 1

    def debug(self, fmt, *args):
        """Add some debug info to the logger."""
        self._logger.debug(fmt, *args)

    def info(self, fmt, *args):
        """Add some general info to the logger."""
        self._logger.info(fmt, *args)
