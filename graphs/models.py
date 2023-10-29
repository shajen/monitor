from django.db.models.functions import TruncMinute, TruncHour, TruncDay, TruncWeek, TruncMonth, TruncYear
from django.db.models import Min, Max, Avg, Count
from django.db import models
from django.utils import timezone
from datetime import timedelta


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

    def get_data(self, aggregation_time, min_max_enabled):
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
            self.measurement_set.annotate(date=trunc("posted_date"))
            .values("date")
            .annotate(min=Min("value"), max=Max("value"), avg=Avg("value"), count=Count("id"))
            .order_by()
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

    class Meta:
        verbose_name = "Sensor group"
        verbose_name_plural = "Sensor groups"

    def __str__(self):
        return "%s" % (self.name)
