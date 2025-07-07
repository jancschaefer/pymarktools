"""pymarktools - A set of markdown utilities for Python."""

import logging

from .core.markdown import DeadImageChecker, DeadLinkChecker, ImageInfo, LinkInfo
from .core.refactor import FileReference, FileReferenceManager

__version__ = "0.1.0"
__all__ = [
    "DeadLinkChecker",
    "DeadImageChecker",
    "LinkInfo",
    "ImageInfo",
    "FileReferenceManager",
    "FileReference",
]

logger = logging.getLogger(__name__)


def greet():
    """Welcome message for pymarktools."""
    logger.info("Welcome to pymarktools - your set of markdown utilities for Python!")
