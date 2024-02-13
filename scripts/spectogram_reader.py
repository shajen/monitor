from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.utils.timezone import make_aware
from sdr.models import *
from humanize import naturalsize

import logging
import numpy as np
import re
import struct
import scripts.utils


class SpectrogramReader:
    def __init__(self):
        self.__logger = logging.getLogger("Spectrogram")
        self.__aggregate_seconds = 24 * 60 * 60
        self.__regex = re.compile("sdr/(\w+)/spectrogram")

    def get_device(self, name):
        try:
            return Device.objects.get(raw_name=name)
        except ObjectDoesNotExist:
            return Device.objects.create(name=name, raw_name=name)

    def round_down_date(self, date):
        return date.replace(hour=0, minute=0, second=0, microsecond=0)

    def round_up_date(self, date):
        return date.replace(hour=23, minute=59, second=59, microsecond=999999)

    def check_spectrogram_integrity(self, s):
        y_size = np.frombuffer(s.labels, dtype=np.uint64).size
        x_size = (s.end_frequency - s.begin_frequency) // s.step_frequency + 1
        data = np.memmap(s.data_file.path, dtype=np.uint8, mode="r", shape=(y_size, x_size))
        self.__logger.info("total data shape: %s, size: %s" % (str(data.shape), naturalsize(data.size)))

    def append_spectrogram(self, device, dt, begin_frequency, end_frequency, step_frequency, data):
        self.__logger.debug(
            "save, %s, %s, %d - %d, %s, %.2f dBfs"
            % (device, dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3], begin_frequency, end_frequency, naturalsize(data.size), np.mean(data))
        )
        begin_model_date = self.round_down_date(dt)
        end_model_date = self.round_up_date(dt)
        device = self.get_device(device)
        try:
            s = Spectrogram.objects.get(
                device=device,
                begin_frequency=begin_frequency,
                end_frequency=end_frequency,
                step_frequency=step_frequency,
                begin_model_date=begin_model_date,
                end_model_date=end_model_date,
            )
        except Spectrogram.DoesNotExist:
            f = (begin_frequency + end_frequency) // 2
            dir = "device_%d/spectrogram" % device.id
            (filename, filename_full) = scripts.utils.get_filename(
                dir, begin_model_date, "%s_%d_%d.bin" % (begin_model_date.strftime("%H_%M_%S"), f, step_frequency), True
            )
            s = Spectrogram.objects.create(
                device=device,
                begin_frequency=begin_frequency,
                end_frequency=end_frequency,
                step_frequency=step_frequency,
                begin_model_date=begin_model_date,
                end_model_date=end_model_date,
                begin_real_date=dt,
                end_real_date=dt,
                data_file=filename,
            )

        with open(s.data_file.path, "ab") as file:
            file.write(data.tobytes())
        s.labels += np.array([int(dt.timestamp() * 1000)]).astype(np.uint64).tobytes()
        s.end_real_date = dt
        s.save()
        # self.check_spectrogram_integrity(s)

    def on_message(self, client, message):
        topic = message.topic
        m = self.__regex.match(topic)
        if m:
            (timestamp, begin_frequency, end_frequency, step_frequency, samples_count) = struct.unpack("<QLLLL", message.payload[:24])
            dt = make_aware(timezone.datetime.fromtimestamp(timestamp / 1000))
            powers = np.array(struct.unpack("<%db" % samples_count, message.payload[24:])).astype(np.int8)
            self.append_spectrogram(m.group(1), dt, begin_frequency, end_frequency, step_frequency, powers)
            return True
        return False
