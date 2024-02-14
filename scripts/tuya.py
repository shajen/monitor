#!/usr/bin/python3

import logging
import math
import monitor.settings as settings
import threading
import time

from sdr.models import *
from tuya_iot import TuyaOpenAPI
from graphs.models import *
from django.core.exceptions import ObjectDoesNotExist


class Tuya(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        config = settings.TUYA
        self.__is_runnig = True
        self.__last_call_timestamp = 0.0
        self.__call_interval = 60
        self.__logger = logging.getLogger("Tuya")
        self.__openapi = TuyaOpenAPI(config["endpoint"], config["access_id"], config["access_key"])
        self.__openapi.connect(config["user"], config["password"], "48", "SmartLife")

    def run(self):
        while self.__is_runnig:
            now = time.time()
            if self.__last_call_timestamp + self.__call_interval < now:
                self.__last_call_timestamp = now
                try:
                    self.__process_device("bfde298182fe64146dinxj")  # klonowa
                except Exception as e:
                    self.__logger.warn("exception: %s" % e)
            time.sleep(1)

    def stop(self):
        self.__is_runnig = False

    def __get_sensor_type(self, type, unit):
        try:
            return SensorType.objects.get(raw_name=type)
        except ObjectDoesNotExist:
            return SensorType.objects.create(name=type, raw_name=type, unit=unit)

    def __get_sensor(self, serial, type, unit):
        try:
            sensor = Sensor.objects.get(serial=serial)
            sensor.update_last_measurement_date()
            return sensor
        except ObjectDoesNotExist:
            sensors_type = self.__get_sensor_type(type, unit)
            sensor = Sensor.objects.create(serial=serial, name=serial, sensor_type=sensors_type)
            return sensor

    def __add_measurement(self, serial, type, unit, value):
        self.__logger.info("new measurement, serial: %s, type: %s, value: %s %s" % (serial, type, value, unit))
        if math.isnan(float(value)):
            self.__logger.warning(
                "invalid measurement value, serial: %s, type: %s, value: %s %s" % (serial, type, value, unit)
            )
        else:
            sensor = self.__get_sensor(serial, type, unit)
            Measurement.objects.create(sensor=sensor, value=value)

    def __parse_device(self, serial, status):
        for data in status["result"]:
            name = data["code"]
            value = data["value"]
            self.__logger.debug("new data, name: %s, value %s" % (name, value))
            if name == "temp_set":
                self.__add_measurement(serial + "_temperature_target", "temperature", "℃", value / 10.0)
            if name == "temp_current":
                self.__add_measurement(serial + "_temperature_current", "temperature", "℃", value / 10.0)
            if name == "switch":
                self.__add_measurement(serial + "_switch", "bool", "", 1 if value else 0)
            if name == "mode":
                self.__add_measurement(serial + "_manual", "bool", "", 1 if value == "manual" else 0)
            if name == "valve_state":
                self.__add_measurement(serial + "_valve", "bool", "", 1 if value == "working" else 0)

    def __process_device(self, device):
        self.__parse_device(device, self.__openapi.get("/v1.0/iot-03/devices/{}/status".format(device)))
