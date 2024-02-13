from dateutil.relativedelta import relativedelta
from django.contrib.admin.views.decorators import staff_member_required as login_required
from django.contrib.auth.decorators import permission_required
from django.db.models import Prefetch
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.timezone import make_aware
from django.views.decorators.http import require_http_methods
from graphs.models import *
from monitor.settings import FALLBACK_API_KEY
from urllib.parse import urlencode
import datetime


@require_http_methods(["GET"])
def get_datetime_range(request):
    now = timezone.now()
    last_count = request.GET.get("last_count", "")
    last_type = request.GET.get("last_type", "")
    datetime_begin = request.GET.get("datetime_begin", "")
    datetime_end = request.GET.get("datetime_end", "")

    if last_count and last_type:
        return (now - relativedelta(**{last_type: int(last_count)}), make_aware(datetime.datetime.max))
    else:
        if datetime_begin:
            datetime_begin = datetime.datetime.strptime(datetime_begin, "%Y-%m-%d %H:%M")
        else:
            datetime_begin = datetime.datetime.min
        if datetime_end:
            datetime_end = datetime.datetime.strptime(datetime_end, "%Y-%m-%d %H:%M")
        else:
            datetime_end = datetime.datetime.max
        return (make_aware(datetime_begin), make_aware(datetime_end))


@require_http_methods(["GET"])
def temperature_measurement_add(request):
    data = {"status": 0}
    errors = []

    try:
        serial = request.GET["serial"]
        value = request.GET["temperature"]
        key = request.GET["key"]
        if key == FALLBACK_API_KEY:
            sensor = Sensor.objects.filter(serial=serial).first()
            if not sensor:
                sensorType = SensorType.objects.filter(raw_name="temperature").first()
                if not sensorType:
                    sensorType = SensorType.objects.create(raw_name="temperature")
                sensor = Sensor.objects.create(serial=serial, sensor_type=sensorType)
            else:
                sensor.update_last_measurement_date()
            Measurement.objects.create(sensor=sensor, value=value)
            data["status"] = 100
        else:
            data["status"] = 101
            errors.append("Wrong key!")
    except:
        data["status"] = 102
        errors.append("Wrong parameters!")

    data["errors"] = errors
    return JsonResponse(data)


@login_required()
@permission_required("graphs.view_sensor", raise_exception=True)
def prefetch_sensors_measurement(request, sensors):
    (datetime_begin, datetime_end) = get_datetime_range(request)
    measurements = Measurement.objects.filter(posted_date__range=(datetime_begin, datetime_end)).order_by("posted_date")
    return sensors.prefetch_related(Prefetch("measurement_set", queryset=measurements))


@login_required()
@permission_required("graphs.view_sensor", raise_exception=True)
def get_sensors(request):
    try:
        group = SensorsGroup.objects.filter(id=request.GET["group_id"], visible=True).first()
        sensors = group.sensors.filter_latest().order_by("name").all()
        name = group.name
        preset = group.preset
    except:
        try:
            sensorType = SensorType.objects.filter(id=request.GET["sensor_type_id"], visible=True).first()
            sensors = Sensor.objects.filter_latest().filter(visible=True, sensor_type=sensorType).order_by("name")
            name = sensorType.name
            preset = None
        except:
            try:
                sensors = Sensor.objects.filter_latest().filter(id=request.GET["sensor_id"], visible=True)
                name = sensors.first().name
                preset = None
            except:
                sensors = Sensor.objects.none()
                name = ""
                preset = None
    return (sensors, name, preset)


@require_http_methods(["GET"])
@login_required()
@permission_required("graphs.view_sensor", raise_exception=True)
def graphs(request):
    if request.GET.get("format", None) == "json":
        data = {"status": 0}
        aggregation_time = request.GET.get("aggregation_time", "minute")
        min_max_enabled = "min_max" in request.GET
        (sensors, data["name"], _) = get_sensors(request)
        (datetime_begin, datetime_end) = get_datetime_range(request)
        data["sensors"] = [s.get_data(datetime_begin, datetime_end, aggregation_time, min_max_enabled) for s in sensors]
        return JsonResponse(data, safe=False)
    else:
        (_, name, preset) = get_sensors(request)
        if "aggregation_time" not in request.GET and preset:
            q = request.META["QUERY_STRING"]
            return redirect(reverse("graphs") + "?" + q + "&" + urlencode(preset.get_params()))
        return render(request, "graphs.html", {"name": name})
