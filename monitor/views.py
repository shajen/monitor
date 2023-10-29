from django.db.models import Q
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.http import FileResponse, HttpResponse
from datetime import timedelta
from collections import Counter
from functools import reduce
import mimetypes
import os


def group_list(counter, group_size):
    if not counter:
        return []
    counter2 = []
    start = 0
    sum = counter[0][1]
    for i in range(1, len(counter)):
        ((start_field_value, start_field_name), _) = counter[start]
        ((prev_field_value, prev_field_name), _) = counter[i - 1]
        ((curr_field_value, curr_field_name), curr_count) = counter[i]
        if prev_field_value + group_size < curr_field_value:
            counter2.append((start_field_value, prev_field_value, start_field_name, prev_field_name, sum))
            start = i
            sum = curr_count
        else:
            sum += curr_count
    ((start_field_value, start_field_name), _) = counter[start]
    ((end_field_value, end_field_name), _) = counter[len(counter) - 1]
    counter2.append((start_field_value, end_field_value, start_field_name, end_field_name, sum))
    return counter2


def filter_data(request, objects, data):
    filters = {}

    for (field, field_name, type_key, _) in data:
        value_sub = request.GET.get(field + "_sub")
        value_exact = request.GET.get(field + "_exact")
        value_min = request.GET.get(field + "_min")
        value_max = request.GET.get(field + "_max")

        if value_sub and type_key == "string":
            filters[field_name + "__icontains"] = value_sub
        if value_exact and type_key == "number":
            filters[field_name] = value_exact
        if value_exact and type_key == "timedelta":
            filters[field_name] = timedelta(seconds=float(value_exact))
        if value_min and type_key == "number":
            filters[field_name + "__gte"] = value_min
        if value_max and type_key == "number":
            filters[field_name + "__lte"] = value_max
        if value_min and type_key == "timedelta":
            filters[field_name + "__gte"] = timedelta(seconds=float(value_min))
        if value_max and type_key == "timedelta":
            filters[field_name + "__lte"] = timedelta(seconds=float(value_max))

    additional_data = {}
    objects = objects.filter(**filters)
    filters = []
    for (field, field_name, type_key, group_size) in data:
        if 0 <= group_size:
            subfilters = []
            for get_key in request.GET.keys():
                if get_key.startswith(field + "_range_"):
                    values = get_key.split("_")
                    q1 = {field + "__gte": values[-2]}
                    q2 = {field + "__lte": values[-1]}
                    subfilters.append(Q(**q1) & Q(**q2))
                if get_key.startswith(field + "_select_"):
                    value = get_key.replace(field + "_select_", "")
                    q = {field: value}
                    subfilters.append(Q(**q))
            if subfilters:
                filters.append(reduce(lambda x, y: x | y, subfilters))

            counter = Counter(objects.order_by(field).values_list(field, field_name))
            if type_key == "string":
                counter = sorted(counter.items(), key=lambda s: s[0][1].lower())
            else:
                counter = sorted(counter.items())
            if 0 < group_size:
                counter = group_list(counter, group_size)
            else:
                counter = [(field_value, field_value, field_name, field_name, c) for ((field_value, field_name), c) in counter]
            additional_data[field + "_list"] = counter

    if filters:
        objects = objects.filter(reduce(lambda x, y: x & y, filters))

    params = request.GET.dict()
    params.pop("order_by", None)
    params = ["%s=%s" % (key, value) for (key, value) in params.items()]
    additional_data["params"] = "&".join(params)
    return (objects, additional_data)


def page_response(request, template, objects, order_by, **kwargs):
    cookie_name = request.path.replace("/", "") + "_params"
    if not request.GET and cookie_name in request.COOKIES and request.COOKIES[cookie_name]:
        return redirect(request.path + "?" + request.COOKIES[cookie_name])
    additional_data = kwargs.get("additional_data", {})
    objects_per_page = kwargs.get("objects_per_page", 100)
    objects_per_page = request.GET.get("objects_per_page", objects_per_page)
    page = request.GET.get("page")
    paginator = Paginator(objects, objects_per_page)
    paginator_page = paginator.get_page(page)
    data = {"page": paginator_page, "objects": paginator_page.object_list, "total_count": paginator.count, "order_by": order_by}
    data = {**data, **additional_data}
    response = render(request, template, data)
    response.set_cookie(cookie_name, "&".join(["%s=%s" % (key, value) for (key, value) in request.GET.items()]))
    return response


def file_response(filename, download_filename=None, remove=True):
    mime = mimetypes.MimeTypes()
    content_type = mime.guess_type(filename)[0]
    if not download_filename:
        download_filename = filename
    response = FileResponse(open(filename, "rb"), content_type=content_type, filename=download_filename)
    if remove:
        os.remove(filename)
    return response


def data_as_file_response(filename, data):
    response = HttpResponse(content_type="application/octet-stream")
    response["Content-Disposition"] = "attachment; filename=%s" % filename
    response.write(data)
    return response
