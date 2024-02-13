from sdr.models import *
from sdr.signals import *
from django.utils import timezone
from django.utils.timezone import localtime

import scripts.utils
import tflite_runtime.interpreter as tflite
import numpy as np
import csv
import io
import os
import time
import threading
import logging


class Classifier(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.__is_working = True
        self.__logger = logging.getLogger("Classifier")
        # https://www.tensorflow.org/lite/inference_with_metadata/task_library/audio_classifier
        # https://tfhub.dev/google/yamnet/1
        self.__logger.info("loading model")
        self.__interpreter = tflite.Interpreter(model_path="ai/yamnet.tflite")
        self.__class_names = self.class_names_from_csv(open("ai/yamnet_class_map.csv").read())

    def get_audio_class_id(self, subname):
        if subname in ["Speech", "Unknown"]:
            name = subname
        else:
            name = "Noise"
        return AudioClass.objects.get_or_create(name=name, subname=subname)[0].id

    def class_names_from_csv(self, class_map_csv_text):
        class_map_csv = io.StringIO(class_map_csv_text)
        class_names = [display_name for (class_index, mid, display_name) in csv.reader(class_map_csv)]
        class_names = class_names[1:]
        return class_names

    def classifiy(self, waveform):
        input_details = self.__interpreter.get_input_details()
        waveform_input_index = input_details[0]["index"]
        output_details = self.__interpreter.get_output_details()
        scores_output_index = output_details[0]["index"]
        embeddings_output_index = output_details[1]["index"]
        spectrogram_output_index = output_details[2]["index"]

        self.__interpreter.resize_tensor_input(waveform_input_index, [len(waveform)], strict=True)
        self.__interpreter.allocate_tensors()
        self.__interpreter.set_tensor(waveform_input_index, waveform)
        self.__interpreter.invoke()
        scores, embeddings, spectrogram = (
            self.__interpreter.get_tensor(scores_output_index),
            self.__interpreter.get_tensor(embeddings_output_index),
            self.__interpreter.get_tensor(spectrogram_output_index),
        )
        return self.__class_names[scores.mean(axis=0).argmax()]

    def get_class(self, t):
        try:
            sample_rate = t.end_frequency - t.begin_frequency
            if t.group.modulation in ["FM", "AM"] and os.path.isfile(t.data_file.path):
                data = np.memmap(t.data_file.path, dtype=np.uint8, mode="r")
                factor = t.sample_size
                data = data[: factor * (t.data_file.size // factor)].reshape(-1, factor)
                (data, sample_rate) = decode(data, sample_rate, t.group.modulation)
                data = data.astype(np.float32)
                return self.classifiy(data)
            else:
                return "Unknown"
        except Exception as e:
            self.__logger.warn("exception: %s" % e)
            return "Unknown"

    def run(self):
        default_audio_class_id = scripts.utils.get_default_audio_class_id()
        self.__logger.debug("start")
        while self.__is_working:
            self.__logger.debug("processing")
            now = timezone.now()
            cut_dt = now - timezone.timedelta(minutes=1)
            for t in Transmission.objects.filter(end_date__lt=cut_dt, audio_class_id=default_audio_class_id).order_by("-end_date").all():
                class_name = self.get_class(t)
                t.audio_class_id = self.get_audio_class_id(class_name)
                t.save()
                self.__logger.info("transmission, id: %d, frequency: %d Hz, date: %s, class: %s " % (t.id, t.middle_frequency(), localtime(t.end_date), class_name))
                if not self.__is_working:
                    break
            time.sleep(1)
        self.__logger.debug("stop")

    def stop(self):
        self.__is_working = False
