import os

from django.conf import settings
from django.http import Http404


def safe_media_path(subdir, filename):
    """
    Return the absolute path of ``filename`` inside ``MEDIA_ROOT/subdir``.

    Raises Http404 if the resolved path escapes that directory (path
    traversal, absolute paths, symlinks pointing elsewhere) or if it is
    not an existing regular file.
    """
    base_dir = os.path.realpath(os.path.join(settings.MEDIA_ROOT, subdir))
    requested_path = os.path.realpath(os.path.join(base_dir, filename))

    if not requested_path.startswith(base_dir + os.sep):
        raise Http404("File not found")
    if not os.path.isfile(requested_path):
        raise Http404("File not found")

    return requested_path
