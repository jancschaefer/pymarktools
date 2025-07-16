"""pymarktools - A set of markdown utilities for Python."""

import logging

from .core.markdown import DeadImageChecker, DeadLinkChecker, ImageInfo, LinkInfo
from .core.refactor import FileReference, FileReferenceManager

__version__ = "0.3.0"
__all__ = [
    "DeadLinkChecker",
    "DeadImageChecker",
    "LinkInfo",
    "ImageInfo",
    "FileReferenceManager",
    "FileReference",
]

logger = logging.getLogger(__name__)

logger.debug("pymarktools initialized with version %s", __version__)
