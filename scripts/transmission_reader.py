from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.utils.timezone import make_aware
from sdr.models import *
from humanize import naturalsize
from django.db.models import F
from sdr.views import get_default_group_id

import logging
import re
import struct
import scripts.utils


class TransmissionReader:
    def __init__(self):
        self.__logger = logging.getLogger("Transmission")
        self.__regex_old = re.compile("sdr/\w+/transmission")
        self.__regex = re.compile("sdr/(\w+)/transmission/(\w+)")

    def get_device(self, name):
        try:
            return Device.objects.get(raw_name=name)
        except ObjectDoesNotExist:
            return Device.objects.create(name=name, raw_name=name)

    def append_transmission(self, device, dt, begin_frequency, end_frequency, samples, sample_size, sample_type):
        self.__logger.debug(
            "%s, append, %s, %d - %d, samples: %d, type: %s"
            % (
                device,
                dt.strftime("%Y-%m-%d %H:%M:%S.%f"),
                begin_frequency,
                end_frequency,
                sample_size,
                sample_type,
            )
        )
        device = self.get_device(device)
        frequency = (begin_frequency + end_frequency) // 2
        try:
            group_id = (
                Group.objects.annotate(bandwidth=F("end_frequency") - F("begin_frequency"))
                .order_by("bandwidth")
                .filter(begin_frequency__lte=frequency, end_frequency__gte=frequency)[0]
                .id
            )
        except:
            group_id = get_default_group_id()
        try:
            t = Transmission.objects.get(
                device=device,
                begin_frequency=begin_frequency,
                end_frequency=end_frequency,
                end_date__gt=dt - timezone.timedelta(seconds=1),
                end_date__lt=dt,
                sample_size=sample_size,
                data_type=sample_type,
                group_id=group_id,
            )
            t.end_date = dt
        except Transmission.DoesNotExist:
            dir = "device_%d/transmission" % device.id
            (filename, filename_full) = scripts.utils.get_filename(
                dir, dt, "%s_%d_%s.bin" % (dt.strftime("%H_%M_%S"), (begin_frequency + end_frequency) // 2, sample_type), True
            )
            t = Transmission.objects.create(
                device=device,
                begin_frequency=begin_frequency,
                end_frequency=end_frequency,
                begin_date=dt,
                end_date=dt,
                sample_size=sample_size,
                data_file=filename,
                data_type=sample_type,
                group_id=group_id,
                audio_class_id=scripts.utils.get_default_audio_class_id(),
            )
        self.__logger.debug("new size: %d = %d x %d, size: %s" % (len(samples), len(samples) / sample_size, sample_size, naturalsize(sample_size)))
        with open(t.data_file.path, "ab") as file:
            file.write(samples)
        t.end_date = dt
        t.save()

    def on_message(self, client, message):
        topic = message.topic
        if self.__regex_old.match(topic):
            self.__logger.debug(topic)
            topic += "/uint8"
        m = self.__regex.match(topic)
        if m:
            self.__logger.debug(topic)
            (timestamp, begin_frequency, end_frequency, samples_count) = struct.unpack("<QLLL", message.payload[:20])
            dt = make_aware(timezone.datetime.fromtimestamp(timestamp / 1000))
            self.append_transmission(m.group(1), dt, begin_frequency, end_frequency, message.payload[20:], samples_count, m.group(2))
            return True
        return False
