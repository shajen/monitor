from collections import defaultdict

import hashlib
import json
import logging
import re


class ISpindel:
    def __init__(self):
        self.__logger = logging.getLogger("ISpindel")
        self.__device_interval = defaultdict(lambda: 60)
        self.__ignored_measurements = ["temp_units"]
        self.__units_map = {
            "tilt": "",
            "temperature": "°C",
            "battery": "V",
            "gravity": "°Blg",
            "rssi": "dBm",
        }

    def publish_device_online(self, client, name, measurement, unit, interval, value):
        self.__logger.debug("publish status online")
        client.publish("%s/status" % (name), payload="online")

    def publish_sensor_config(self, client, name, measurement, unit, interval, value):
        self.__logger.debug("publish config")
        sensor_raw = "%s_%s" % (name, measurement)
        name_id = hashlib.md5(name.encode("utf-8")).hexdigest()
        sensor_id = hashlib.md5(sensor_raw.encode("utf-8")).hexdigest()
        config = {
            "unit_of_measurement": unit,
            "expire_after": interval + 15,
            "name": measurement,
            "state_topic": "%s/sensor/%s/state" % (name, measurement),
            "availability_topic": "%s/status" % name,
            "unique_id": sensor_id,
            "device": {
                "identifiers": name_id,
                "name": name,
            },
        }
        client.publish("homeassistant/sensor/%s/%s/config" % (name, measurement), payload=json.dumps(config))

    def publish_sensor_data(self, client, name, measurement, unit, interval, value):
        self.__logger.info("publish, name: %s, measurement: %s, value: %.2f %s" % (name, measurement, value, unit))
        client.publish("%s/sensor/%s/state" % (name, measurement), payload="%.2f" % value)

    def on_sensor(self, client, name, measurement, unit, interval, value):
        self.publish_device_online(client, name, measurement, unit, interval, value)
        self.publish_sensor_config(client, name, measurement, unit, interval, value)
        self.publish_sensor_data(client, name, measurement, unit, interval, value)

    def on_message(self, client, message):
        topic = message.topic
        try:
            payload = message.payload.decode("utf-8")
        except:
            return False
        m = re.match("ispindel/(\w+)/(\w+)", topic)
        if m:
            name = m.group(1).lower()
            measurement = m.group(2).lower()
            if re.match("tilt|temperature|battery|gravity|rssi", measurement):
                unit = self.__units_map[measurement]
                self.on_sensor(client, name, measurement, unit, self.__device_interval[name], float(payload))
                return True
            elif measurement == "interval":
                self.__device_interval[name] = int(payload)
                return True
            elif measurement in self.__ignored_measurements:
                return True
        return False
