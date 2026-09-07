#!/usr/bin/env python
import os
import sys


def main():
    if sys.platform == "darwin" and os.path.isdir("/opt/homebrew/lib"):
        # WeasyPrint (xuất PDF) load Pango qua cffi/dlopen - trên macOS + Homebrew,
        # dyld không tự tìm ra .dylib trong /opt/homebrew/lib trừ khi khai báo qua
        # biến này. Không ảnh hưởng gì trong Docker/Linux (không dùng DYLD_*).
        os.environ.setdefault("DYLD_FALLBACK_LIBRARY_PATH", "/opt/homebrew/lib")

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "teaching_scheduler.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
