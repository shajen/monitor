from django.core.exceptions import ObjectDoesNotExist
from graphs.models import *

import logging
import math
import re


class HomeAssistant:
    def __init__(self):
        self.__logger = logging.getLogger("HomeAssistant")
        self.__ignored_measurements = ["ip", "ssid", "version"]
        self.__units_map = {
            "temperature": "℃",
            "vcc": "V",
            "voltage": "V",
            "battery": "V",
            "gravity": "°Blg",
            "tilt": "°",
            "uptime": "s",
            "wifi_signal": "dBm",
            "power": "W",
            "current": "A",
            "energy": "kWh",
            "resistance": "Ω",
            "pressure": "hPa",
            "humidity": "%",
            "pm10": "µg/m³",
            "pm2_5": "µg/m³",
            "rssi": "dBm",
            "iaq": "",
            "co2": "",
            "breath_voc": "",
        }

    def get_type_and_unit(self, measurement):
        for type in self.__units_map.keys():
            if type in measurement:
                return (type, self.__units_map[type])
        raise Exception("Can not map %s to (type, unit)." % (measurement))

    def get_sensor_type(self, type, unit):
        try:
            return SensorType.objects.get(raw_name=type)
        except ObjectDoesNotExist:
            return SensorType.objects.create(name=type, raw_name=type, unit=unit)

    def on_sensor(self, device, measurement, type, unit, value):
        self.__logger.info("publish, device: %s, measurement: %s, type: %s, value: %s %s" % (device, measurement, type, value, unit))
        serial = "%s_%s" % (device, measurement)
        name = "%s %s" % (device, measurement)
        try:
            sensor = Sensor.objects.get(serial=serial)
            sensor.update_last_measurement_date()
        except ObjectDoesNotExist:
            sensors_type = self.get_sensor_type(type, unit)
            sensor = Sensor.objects.create(serial=serial, name=name, sensor_type=sensors_type)
        Measurement.objects.create(sensor=sensor, value=value)

    def on_message(self, client, message):
        topic = message.topic
        try:
            payload = message.payload.decode("utf-8")
        except:
            return False
        m = re.match("(\w+)/sensor/(\w+)/state", topic)
        if m:
            device = m.group(1)
            measurement = m.group(2)
            if any([sm in measurement for sm in self.__ignored_measurements]):
                self.__logger.debug("ignored_measurement, topic: %s" % (topic))
                return True
            value = float(payload)
            (type, unit) = self.get_type_and_unit(measurement)
            if math.isnan(value):
                self.__logger.info(
                    "invalid value, device: %s, measurement: %s, type: %s, value: %s %s"
                    % (device, measurement, type, value, unit)
                )
                return False
            else:
                self.on_sensor(device, measurement, type, unit, value)
                return True
        return False
