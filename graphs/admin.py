from django.contrib import admin
from graphs.models import *
from monitor.settings import FULL_MODE_ENABLED


class SensorTypeAdmin(admin.ModelAdmin):
    list_per_page = 100
    list_display = ("id", "name", "raw_name", "digits", "unit", "visible", "posted_date")


class SensorsInline(admin.TabularInline):
    model = SensorsGroup.sensors.through


class SensorAdmin(admin.ModelAdmin):
    list_per_page = 100
    list_display = ("id", "name", "serial", "sensor_type", "visible", "posted_date", "last_measurement_date")
    inlines = [SensorsInline]


class MeasurementAdmin(admin.ModelAdmin):
    list_per_page = 100
    list_display = ("id", "sensor", "value", "posted_date")


class SensorsGroupAdmin(admin.ModelAdmin):
    list_per_page = 100
    list_display = ("id", "name", "visible", "preset", "posted_date")
    filter_horizontal = ("sensors",)


class PresetAdmin(admin.ModelAdmin):
    list_per_page = 100
    list_display = ("id", "begin_date", "end_date", "last_count", "last_type", "aggregation_time", "min_max")


if FULL_MODE_ENABLED:
    admin.site.register(SensorType, SensorTypeAdmin)
    admin.site.register(Sensor, SensorAdmin)
    admin.site.register(Measurement, MeasurementAdmin)
    admin.site.register(SensorsGroup, SensorsGroupAdmin)
    admin.site.register(Preset, PresetAdmin)
