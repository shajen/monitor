import threading
import logging
import django.db
import time
import paho.mqtt.client

from scripts.spectogram_reader import SpectrogramReader
from scripts.transmission_reader import TransmissionReader
from scripts.ispindel import ISpindel
from scripts.home_assistant import HomeAssistant


class Reader(threading.Thread):
    def __init__(self, config):
        threading.Thread.__init__(self)
        self.__logger = logging.getLogger("Reader")

        self.__parsers = []
        self.__parsers.append(SpectrogramReader())
        self.__parsers.append(TransmissionReader())
        self.__parsers.append(ISpindel())
        self.__parsers.append(HomeAssistant())

        self.__client = paho.mqtt.client.Client(paho.mqtt.client.CallbackAPIVersion.VERSION1)
        self.__client.username_pw_set(config["user"], config["password"])
        self.__client.user_data_set(self)
        self.__client.connect(config["host"], config["port_tcp"])
        self.__client.on_connect = Reader.on_connect
        self.__client.on_message = Reader.on_message

    def run(self):
        self.__client.loop_forever()

    def stop(self):
        self.__client.disconnect()

    def on_connect(client, userdata, flags, rc):
        self = userdata
        self.__logger.info("connected")
        self.__client.subscribe("ispindel/+/+")
        self.__client.subscribe("+/sensor/+/state")
        self.__client.subscribe("sdr/+/spectrogram")
        self.__client.subscribe("sdr/+/transmission")
        self.__client.subscribe("sdr/+/transmission/+")

    def on_message(client, userdata, message):
        self = userdata
        django.db.reset_queries()
        django.db.close_old_connections()
        for parser in self.__parsers:
            try:
                if parser.on_message(client, message):
                    return True
            except django.db.OperationalError:
                self.__logger.warn("reset db connection")
                django.db.connection.close()
            except Exception as e:
                pass
                self.__logger.warn("exception: %s" % e)
        self.__logger.warn("can not parse, topic: %s" % (message.topic))
