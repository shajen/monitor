#!/usr/bin/python3

import logging
import time
import argparse
import shlex
import monitor.settings as settings

from scripts.reader import Reader
from scripts.tuya import Tuya
from scripts.cleaner import Cleaner


def run(*args):
    parser = argparse.ArgumentParser(description="Set worker config")
    parser.add_argument("-r", "--reader", help="enable reader", action="store_true")
    parser.add_argument("-t", "--tuya", help="enable tuya", action="store_true")
    parser.add_argument("-clr", "--cleaner", help="enable cleaner", action="store_true")
    parser.add_argument("-ss", "--spectrograms_total_size_gb", help="set spectrograms quota in gb", type=int, default=0, metavar="size")
    parser.add_argument("-ts", "--transmissions_total_size_gb", help="set transmissions quota in gb", type=int, default=0, metavar="size")
    parser.add_argument("-cls", "--classifier", help="enable classifier", action="store_true")
    args = parser.parse_args(shlex.split(args[0] if len(args) else ""))

    logging.getLogger("Reader").setLevel(logging.INFO)
    logging.getLogger("Tuya").setLevel(logging.INFO)
    logging.getLogger("ISpindel").setLevel(logging.INFO)
    logging.getLogger("HomeAssistant").setLevel(logging.INFO)
    logging.getLogger("Spectrogram").setLevel(logging.INFO)
    logging.getLogger("Transmission").setLevel(logging.INFO)
    logging.getLogger("Cleaner").setLevel(logging.INFO)
    logging.getLogger("Classifier").setLevel(logging.INFO)

    threads = []
    if args.reader:
        threads.append(Reader(settings.MQTT))
    if args.tuya:
        threads.append(Tuya())
    if args.cleaner:
        threads.append(Cleaner(args.spectrograms_total_size_gb, args.transmissions_total_size_gb))
    if args.classifier:
        from scripts.classifier import Classifier

        threads.append(Classifier())

    for t in threads:
        t.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        for t in threads:
            t.stop()

    for t in threads:
        t.join()
