from datetime import timedelta
from django.db import models
from django.db.models import Count, Min, Max, Avg, Count
from django.db.models.functions import TruncMinute, TruncHour, TruncDay, TruncWeek, TruncMonth, TruncYear
from django.utils import timezone
from django.utils.timezone import localtime


class Preset(models.Model):
    type_choices = (
        ("minutes", "Minutes"),
        ("hours", "Hours"),
        ("days", "Days"),
        ("weeks", "Weeks"),
        ("months", "Months"),
        ("years", "Years"),
    )
    aggregation_choices = (
        ("minute", "Minute"),
        ("hour", "Hour"),
        ("day", "Day"),
        ("week", "Week"),
        ("month", "Month"),
        ("year", "Year"),
    )
    begin_date = models.DateTimeField("Początek zakresu", null=True, blank=True)
    end_date = models.DateTimeField("Koniec zakresu", null=True, blank=True)
    last_count = models.PositiveIntegerField("Ostatni zakres (ilość próbek)", null=True, blank=True)
    last_type = models.CharField(
        "Ostatni zakres (typ próbek)", max_length=255, choices=type_choices, default="", blank=True
    )
    aggregation_time = models.CharField("Czas agregacji", max_length=255, choices=aggregation_choices, default="minute")
    min_max = models.BooleanField("Min max", default=False)

    def __str__(self):
        label = ""
        if self.last_count and self.last_type:
            label = "%s %s" % (self.last_count, self.last_type)
        else:
            label = "%s - %s" % (
                localtime(self.begin_date).strftime("%Y-%m-%d %H:%S") if self.begin_date else "",
                localtime(self.end_date).strftime("%Y-%m-%d %H:%S") if self.end_date else "",
            )
        return "%s, agg: %s, min_max: %s" % (label, self.aggregation_time or "", self.min_max)

    def get_params(self):
        params = {
            "datetime_begin": localtime(self.begin_date).strftime("%Y-%m-%d %H:%M") if self.begin_date else "",
            "datetime_end": localtime(self.end_date).strftime("%Y-%m-%d %H:%M") if self.end_date else "",
            "last_count": self.last_count or "",
            "last_type": self.last_type,
            "aggregation_time": self.aggregation_time,
        }
        if self.min_max:
            params["min_max"] = ""
        return params


class SensorType(models.Model):
    name = models.CharField("Nazwa", max_length=255)
    raw_name = models.CharField("Surowa nazwa", max_length=255, unique=True)
    digits = models.IntegerField("Dokładność", default=2)
    unit = models.CharField("Jednostka", max_length=255, blank=True)
    posted_date = models.DateTimeField("Data dodania", auto_now_add=True)
    visible = models.BooleanField("Widoczny", default=True)

    class Meta:
        verbose_name = "Sensor type"
        verbose_name_plural = "Sensor types"

    def __str__(self):
        return "%s (%s)" % (self.name, self.unit)


class SensorManager(models.Manager):
    def filter_latest(self):
        d = timezone.now() - timedelta(days=7)
        return self.filter(last_measurement_date__gte=d)


class Sensor(models.Model):
    name = models.CharField("Nazwa", max_length=255)
    serial = models.CharField("Numer seryjny", max_length=255, unique=True)
    visible = models.BooleanField("Widoczny", default=True)
    sensor_type = models.ForeignKey(SensorType, verbose_name="Typ czujnika", on_delete=models.CASCADE)
    posted_date = models.DateTimeField("Data dodania", auto_now_add=True)
    last_measurement_date = models.DateTimeField("Data ostatniego pomiaru", default=timezone.now)
    objects = SensorManager()

    def __str__(self):
        return "%s (%s)" % (self.name, self.serial)

    def get_data(self, datetime_begin, datetime_end, aggregation_time, min_max_enabled):
        data = {}
        data["name"] = self.name
        data["unit"] = self.sensor_type.unit

        if aggregation_time == "minute":
            trunc = TruncMinute
        elif aggregation_time == "hour":
            trunc = TruncHour
        elif aggregation_time == "day":
            trunc = TruncDay
        elif aggregation_time == "week":
            trunc = TruncWeek
        elif aggregation_time == "month":
            trunc = TruncMonth
        elif aggregation_time == "year":
            trunc = TruncYear
        else:
            trunc = TruncMinute

        measurements = (
            self.measurement_set.filter(posted_date__range=(datetime_begin, datetime_end))
            .annotate(date=trunc("posted_date"))
            .values("date")
            .annotate(min=Min("value"), max=Max("value"), avg=Avg("value"), count=Count("id"))
            .order_by("date")
        )
        data["mean_data"] = [[m["date"].timestamp() * 1000, m["avg"]] for m in measurements]
        if min_max_enabled:
            data["min_max_data"] = [[m["date"].timestamp() * 1000, m["min"], m["max"]] for m in measurements]
        return data

    def update_last_measurement_date(self):
        self.last_measurement_date = timezone.now()
        self.save()


class Measurement(models.Model):
    sensor = models.ForeignKey(Sensor, verbose_name="Czujnik", on_delete=models.CASCADE)
    value = models.FloatField(verbose_name="Wartość")
    posted_date = models.DateTimeField("Data dodania", auto_now_add=True, db_index=True)

    def __str__(self):
        return "%s - %s" % (self.sensor, self.value)


class SensorsGroup(models.Model):
    name = models.CharField("Nazwa", max_length=255)
    visible = models.BooleanField("Widoczna", default=True)
    sensors = models.ManyToManyField(Sensor, verbose_name="Lista czujników")
    posted_date = models.DateTimeField("Data dodania", auto_now_add=True)
    preset = models.ForeignKey(Preset, verbose_name="Preset", null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = "Sensor group"
        verbose_name_plural = "Sensor groups"

    def __str__(self):
        return "%s" % (self.name)
