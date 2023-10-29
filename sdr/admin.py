from django.contrib import admin
from sdr.models import *


class DeviceAdmin(admin.ModelAdmin):
    list_per_page = 100
    list_display = ("id", "name", "raw_name")


class GroupAdmin(admin.ModelAdmin):
    list_per_page = 100
    list_display = (
        "id",
        "name",
        "modulation",
        "begin_frequency",
        "end_frequency",
    )


class SpectrogramAdmin(admin.ModelAdmin):
    list_per_page = 100
    list_display = (
        "id",
        "device",
        "begin_frequency",
        "end_frequency",
        "step_frequency",
        "begin_real_date",
        "end_real_date",
        "begin_model_date",
        "end_model_date",
        "data_file",
    )


class AudioClassAdmin(admin.ModelAdmin):
    list_per_page = 100
    list_display = (
        "id",
        "name",
        "subname",
    )


class TransmissionAdmin(admin.ModelAdmin):
    list_per_page = 100
    list_display = (
        "id",
        "device",
        "middle_frequency",
        "group",
        "audio_class",
        "bandwidth",
        "duration",
        "begin_frequency",
        "end_frequency",
        "begin_date",
        "end_date",
        "data_file",
        "data_type",
    )


admin.site.register(Device, DeviceAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Spectrogram, SpectrogramAdmin)
admin.site.register(AudioClass, AudioClassAdmin)
admin.site.register(Transmission, TransmissionAdmin)
