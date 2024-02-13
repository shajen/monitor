from django.contrib.admin.views.decorators import staff_member_required as login_required
from django.contrib.auth.decorators import permission_required
from django.db.models import F, Count
from django.db.models.functions import TruncSecond, TruncDate, Length
from django.shortcuts import render
from django.utils.timezone import localtime
from django.views.decorators.http import require_http_methods
from monitor.settings import BASE_DIR
from sdr.models import *
from sdr.signals import *
from monitor.views import *
import math
import numpy as np
import sdr.drawer
import uuid
import monitor.settings


def get_download_filename(name, id, extension, dt):
    return "%s%d_%s.%s" % (name, id, localtime(dt).strftime("%Y%m%d_%H%M%S"), extension)


def get_download_raw_iq_filename(name, id, frequency, sample_rate, dt):
    return "%s%d_%s_%d_%d_fc.raw" % (name, id, localtime(dt).strftime("%Y%m%d_%H%M%S"), frequency, sample_rate)


@login_required()
@permission_required("sdr.view_spectrogram", raise_exception=True)
def spectrograms(request):
    order_by = request.GET.get("order_by", "-datetime")
    spectrograms = (
        Spectrogram.objects.select_related("device")
        .annotate(
            device_name=F("device__name"),
            datetime=F("begin_model_date"),
            date=TruncDate("begin_model_date"),
            samples=Length("labels") / 8,
            sample_rate=F("end_frequency") - F("begin_frequency"),
            frequency=F("begin_frequency") + (F("end_frequency") - F("begin_frequency")) / 2,
            duration=TruncSecond("end_real_date") - TruncSecond("begin_real_date"),
        )
        .order_by(order_by, "-datetime", "frequency", "device_name")
    )
    (spectrograms, additional_data) = filter_data(
        request,
        spectrograms,
        [
            ("device_id", "device_name", "string", 0),
            ("date", "date", "number", -1),
            ("samples", "samples", "number", -1),
            ("frequency", "frequency", "number", 0),
            ("sample_rate", "sample_rate", "number", 0),
            ("step_frequency", "step_frequency", "number", 0),
        ],
    )
    return page_response(request, "spectrograms.html", spectrograms, order_by, additional_data=additional_data)


@login_required()
@permission_required("sdr.view_spectrogram", raise_exception=True)
def spectrogram(request, spectrogram_id):
    mode = request.GET.get("mode", "static")
    spectrogram = Spectrogram.objects.annotate(
        samples=Length("labels") / 8,
        sample_rate=F("end_frequency") - F("begin_frequency"),
        frequency=F("begin_frequency") + (F("end_frequency") - F("begin_frequency")) / 2,
        duration=TruncSecond("end_real_date") - TruncSecond("begin_real_date"),
    ).get(id=spectrogram_id)
    return render(request, "spectrogram.html", {"spectrogram": spectrogram, "mode": mode})


@login_required()
@permission_required("sdr.view_spectrogram", raise_exception=True)
def spectrogram_data(request, spectrogram_id):
    format = request.GET.get("format", "image")
    s = Spectrogram.objects.get(id=spectrogram_id)
    if format == "image":
        filename = "tmp_%s.jpg" % uuid.uuid4().hex
        y_labels = np.frombuffer(s.labels, dtype=np.uint64)
        y_size = y_labels.size
        x_size = s.data_file.file.size // y_size
        data = np.memmap(s.data_file.path, dtype=np.int8, mode="r", shape=(y_size, x_size))

        kwargs = {"draw_frequency": False, "draw_power": False, "draw_time": False, "draw_data": False}
        data_type = request.GET.get("data", "")
        if data_type == "left":
            kwargs["draw_time"] = True
        elif data_type == "top":
            kwargs["draw_power"] = True
            kwargs["draw_frequency"] = True
        elif data_type == "main":
            kwargs["draw_data"] = True
        else:
            kwargs = {}

        drawer = sdr.drawer.Drawer(frequency_labels_count=(s.end_frequency - s.begin_frequency) // 200000, **kwargs)
        drawer.draw_spectrogram(data, filename, x_size, y_size, s.begin_frequency, s.end_frequency, y_labels)
        return file_response(filename, get_download_filename("spectrogram", s.id, "jpg", s.begin_real_date))
    elif format == "raw":
        return file_response(s.data_file.path, get_download_filename("spectrogram", s.id, "raw", s.begin_real_date), False)


@login_required()
@permission_required("sdr.view_transmission", raise_exception=True)
def transmissions(request):
    order_by = request.GET.get("order_by", "-end_date")
    transmissions = (
        Transmission.objects.select_related("device")
        .select_related("group")
        .annotate(
            device_name=F("device__name"),
            group_name=F("group__name"),
            modulation=F("group__modulation"),
            datetime=F("begin_date"),
            duration=TruncSecond("end_date") - TruncSecond("begin_date"),
            frequency=F("begin_frequency") + (F("end_frequency") - F("begin_frequency")) / 2,
            class_name=F("audio_class__name"),
            class_subname=F("audio_class__subname"),
        )
        .order_by(order_by, "-end_date", "frequency")
    )
    (transmissions, additional_data) = filter_data(
        request,
        transmissions,
        [
            ("device_id", "device_name", "string", 0),
            ("datetime", "datetime", "number", -1),
            ("duration", "duration", "timedelta", -1),
            ("group_id", "group_name", "string", 0),
            ("frequency", "frequency", "number", 20000),
            ("modulation", "modulation", "string", 0),
            ("class_name", "class_name", "string", 0),
            ("class_subname", "class_subname", "string", 0),
        ],
    )
    return page_response(request, "transmissions.html", transmissions, order_by, additional_data=additional_data)


@login_required()
@permission_required("sdr.view_transmission", raise_exception=True)
def transmission(request, transmission_id):
    transmission = Transmission.objects.annotate(
        duration=TruncSecond("end_date") - TruncSecond("begin_date"),
        sample_rate=F("end_frequency") - F("begin_frequency"),
        frequency=F("begin_frequency") + (F("end_frequency") - F("begin_frequency")) / 2,
    ).get(id=transmission_id)
    return render(request, "transmission.html", {"transmission": transmission})


@login_required()
@permission_required("sdr.view_transmission", raise_exception=True)
def transmission_data(request, transmission_id):
    format = request.GET.get("format")
    t = Transmission.objects.get(id=transmission_id)
    data = np.memmap(t.data_file.path, dtype=np.uint8, mode="r")
    sample_rate = t.end_frequency - t.begin_frequency
    if format == "spectrogram":
        filename = get_download_filename("transmission", t.id, "jpg", t.begin_date)
        data = make_spectrogram(data, sample_rate)
        drawer = sdr.drawer.Drawer(frequency_labels_count=8, draw_time=False, draw_power=True, text_size=16, text_stroke=2, min_width=1024)
        drawer.draw_spectrogram(data, filename, data.shape[1], data.shape[0], t.begin_frequency, t.end_frequency, list(range(data.shape[0])))
        return file_response(filename)
    elif format == "raw":
        filename = get_download_raw_iq_filename("transmission", t.id, t.middle_frequency(), sample_rate, t.begin_date)
        block_size = 10 * 2**10 * 2**10
        if os.path.exists(filename):
            os.remove(filename)
        for i in range(math.ceil(data.size / block_size)):
            with open(filename, "ab") as file:
                file.write(convert_uint8_to_float32(data[i * block_size : (i + 1) * block_size]).tobytes())
        return file_response(filename)
    elif t.group.modulation in ["FM", "AM"]:
        filename = get_download_filename("transmission", t.id, "mp3", t.begin_date)
        factor = t.sample_size
        (data, sample_rate) = decode(data[: factor * (t.data_file.size // factor)].reshape(-1, factor), sample_rate, t.group.modulation)
        save(data, sample_rate, filename)
        return file_response(filename)


@login_required()
@permission_required("sdr.change_group", raise_exception=True)
def groups(request, message_success="", message_error=""):
    order_by = request.GET.get("order_by", "begin_frequency")
    groups = Group.objects.annotate(bandwidth=F("end_frequency") - F("begin_frequency"), transmissions_count=Count("transmission")).order_by(
        order_by, "-bandwidth"
    )
    (groups, additional_data) = filter_data(
        request,
        groups,
        [
            ("name", "name", "string", 0),
            ("begin_frequency", "begin_frequency", "number", -1),
            ("end_frequency", "end_frequency", "number", -1),
            ("modulation", "modulation", "string", 0),
        ],
    )
    additional_data["message_success"] = message_success
    additional_data["message_error"] = message_error
    return page_response(request, "groups.html", groups, order_by, additional_data=additional_data)


def get_default_group_id():
    return Group.objects.get_or_create(name="Default", begin_frequency=0, end_frequency=10000000000, modulation="FM")[0].id


@login_required()
@permission_required("sdr.change_group", raise_exception=True)
def update_groups(request):
    default_group_id = get_default_group_id()
    Transmission.objects.update(group_id=default_group_id)
    for group in sdr.models.Group.objects.annotate(bandwidth=F("end_frequency") - F("begin_frequency")).order_by("-bandwidth").all():
        Transmission.objects.annotate(frequency=(F("begin_frequency") + F("end_frequency")) / 2).filter(
            frequency__gte=group.begin_frequency, frequency__lte=group.end_frequency
        ).update(group_id=group.id)


@login_required()
@permission_required("sdr.change_group", raise_exception=True)
def add_group(request):
    try:
        name = request.GET["name"]
        begin_frequency = int(request.GET["begin_frequency"])
        end_frequency = int(request.GET["end_frequency"])
        modulation = request.GET["modulation"]
        Group.objects.get_or_create(name=name, begin_frequency=begin_frequency, end_frequency=end_frequency, modulation=modulation)
        update_groups(request)
        return groups(request, "Success!", "")
    except:
        return groups(request, "", "Error!")


@login_required()
@permission_required("sdr.change_group", raise_exception=True)
def delete_group(request, group_id):
    try:
        default_group_id = get_default_group_id()
        if int(group_id) == default_group_id:
            return groups(request, "", "Can not delete Default group!")
        else:
            Group.objects.get(id=group_id).transmission_set.update(group_id=default_group_id)
            Group.objects.filter(id=group_id).delete()
            update_groups(request)
            return groups(request, "Success!", "")
    except:
        return groups(request, "", "Error")


@login_required()
@permission_required("sdr.change_device", raise_exception=True)
def config(request):
    return render(request, "config.html", {"mqtt": monitor.settings.MQTT})
