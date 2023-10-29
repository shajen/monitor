from django.db import models
from django.utils.timezone import timedelta
import sdr.signals


class Device(models.Model):
    name = models.CharField("Name", max_length=255)
    raw_name = models.CharField("Raw name", max_length=255, db_index=True, unique=True)

    def __str__(self):
        return self.raw_name


def default_device():
    return Device.objects.get_or_create(raw_name="default")[0].id


class Spectrogram(models.Model):
    begin_frequency = models.PositiveBigIntegerField("Begin (frequency)", db_index=True)
    end_frequency = models.PositiveBigIntegerField("End (frequency)", db_index=True)
    step_frequency = models.PositiveIntegerField("Step (frequency)", db_index=True)
    begin_model_date = models.DateTimeField("Begin (model)", db_index=True)
    end_model_date = models.DateTimeField("End (model)", db_index=True)
    begin_real_date = models.DateTimeField("Begin (data)", db_index=True)
    end_real_date = models.DateTimeField("End (data)", db_index=True)
    labels = models.BinaryField("Labels")
    data_file = models.FileField("Data file", upload_to="spectrogram/%Y-%m-%d/")
    device = models.ForeignKey(Device, on_delete=models.CASCADE, default=default_device)

    class Meta:
        unique_together = ("device", "begin_frequency", "end_frequency", "step_frequency", "begin_model_date", "end_model_date")


class Group(models.Model):
    name = models.CharField("Name", max_length=255, unique=True)
    modulation = models.CharField("Modulation", max_length=255)
    begin_frequency = models.PositiveBigIntegerField("Begin frequency", db_index=True)
    end_frequency = models.PositiveBigIntegerField("End frequency", db_index=True)
    data_type = models.CharField("Data type", max_length=255, default="audio")

    def __str__(self):
        return "%s - %s" % (self.name, self.modulation)


class AudioClass(models.Model):
    name = models.CharField("Name", max_length=255)
    subname = models.CharField("Subname", max_length=255, unique=True)

    class Meta:
        unique_together = ("name", "subname")


class Transmission(models.Model):
    begin_frequency = models.PositiveBigIntegerField("Begin (frequency)", db_index=True)
    end_frequency = models.PositiveBigIntegerField("End (frequency)", db_index=True)
    begin_date = models.DateTimeField("Begin (date)", db_index=True)
    end_date = models.DateTimeField("End (date)", db_index=True)
    sample_size = models.PositiveIntegerField("Sample size", db_index=True)
    data_file = models.FileField("Data file", upload_to="transmission/%Y-%m-%d/")
    data_type = models.CharField("Data type", max_length=255)
    audio_class = models.ForeignKey(AudioClass, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, default=default_device)

    def duration(self):
        return timedelta(seconds=round((self.end_date - self.begin_date).total_seconds()))

    def middle_frequency(self):
        return self.begin_frequency + (self.end_frequency - self.begin_frequency) // 2

    def bandwidth(self):
        return self.end_frequency - self.begin_frequency
