from sdr.models import *

import logging
import threading
import time


class Cleaner(threading.Thread):
    def __init__(self, spectrograms_total_size_gb, transmissions_total_size_gb):
        threading.Thread.__init__(self)
        self.__is_runnig = True
        self.__last_clear_timestamp = 0.0
        self.__clear_interval = 60 * 60
        self.__logger = logging.getLogger("Cleaner")
        self.__spectrograms_total_size_gb = spectrograms_total_size_gb
        self.__transmissions_total_size_gb = transmissions_total_size_gb

    def run(self):
        while self.__is_runnig:
            now = time.time()
            if self.__last_clear_timestamp + self.__clear_interval < now:
                self.__last_clear_timestamp = now
                try:
                    if 0 < self.__spectrograms_total_size_gb:
                        self.__remove_spectrograms()
                    if 0 < self.__transmissions_total_size_gb:
                        self.__remove_transmissions()
                except Exception as e:
                    self.__logger.warn("exception: %s" % e)
            time.sleep(1)

    def stop(self):
        self.__is_runnig = False

    def __remove_spectrograms(self):
        removed = 0
        total_size = 0
        max_size = self.__spectrograms_total_size_gb * 1024 * 1024 * 1024
        objects = []
        for s in Spectrogram.objects.order_by("-begin_real_date"):
            try:
                total_size += s.data_file.size
                if max_size < total_size:
                    removed += 1
                    objects.append(s.id)
                    self.__logger.debug("removing spectrogram: %d, %s" % (s.id, s.begin_real_date))
            except FileNotFoundError:
                removed += 1
                objects.append(s.id)
                self.__logger.debug("removing spectrogram: %d, %s" % (s.id, s.begin_real_date))

        self.__logger.info("spectrograms max size: %.2f GB, current size: %.2f GB" % (self.__spectrograms_total_size_gb, total_size / 1024 / 1024 / 1024))
        Spectrogram.objects.filter(id__in=objects).delete()
        self.__logger.info("removed last %d spectrograms" % removed)

    def __remove_transmissions(self):
        removed = 0
        total_size = 0
        max_size = self.__transmissions_total_size_gb * 1024 * 1024 * 1024
        objects = []
        for t in Transmission.objects.order_by("-begin_date"):
            try:
                total_size += t.data_file.size
                if max_size < total_size:
                    removed += 1
                    objects.append(t.id)
                    self.__logger.debug("removing transmission: %d, %s" % (t.id, t.begin_date))
            except FileNotFoundError:
                removed += 1
                objects.append(t.id)
                self.__logger.debug("removing transmission: %d, %s" % (t.id, t.begin_date))

        self.__logger.info("transmissions max size: %.2f GB, current size: %.2f" % (self.__transmissions_total_size_gb, total_size / 1024 / 1024 / 1024))
        Transmission.objects.filter(id__in=objects).delete()
        self.__logger.info("removed last %d transmissions" % removed)
