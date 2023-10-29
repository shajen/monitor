import os

from django.conf import settings
from sdr.models import *


def get_filename(dir, dt, name, create_empty):
    dir = "%s/%s" % (dir, dt.strftime("%Y-%m-%d"))
    filename = "%s/%s" % (dir, name)
    filename_full = "%s/%s" % (settings.MEDIA_ROOT, filename)
    os.makedirs("%s/%s" % (settings.MEDIA_ROOT, dir), exist_ok=True)
    if create_empty:
        open(filename_full, "wb").close()
    return (filename, filename_full)


def get_default_audio_class_id():
    return AudioClass.objects.get_or_create(name="Default", subname="Default")[0].id
