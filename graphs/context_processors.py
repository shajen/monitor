from graphs.models import *
from django.db.models import Prefetch
from monitor.settings import FULL_MODE_ENABLED


def sensor_groups(request):
    sensors = Sensor.objects.filter_latest().filter(visible=True).values_list("id", flat=True)
    return {"sensors_groups": SensorsGroup.objects.filter(visible=True).order_by("name").filter(sensors__in=list(sensors)).distinct()}


def sensor_types(request):
    return {
        "sensor_types": SensorType.objects.filter(visible=True)
        .order_by("name")
        .prefetch_related(Prefetch("sensor_set", Sensor.objects.filter_latest().filter(visible=True).order_by("name")))
    }


def full_mode_enabled(request):
    return {"full_mode_enabled": FULL_MODE_ENABLED}
