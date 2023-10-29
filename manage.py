#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "monitor.settings")
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
