from django.db import models


class Provider(models.Model):
    name = models.CharField("Name", max_length=255, unique=True)

    def __str__(self):
        return self.name


class Country(models.Model):
    name = models.CharField("Name", max_length=255, unique=True)

    class Meta:
        verbose_name = "Contry"
        verbose_name_plural = "Countries"

    def __str__(self):
        return self.name


class City(models.Model):
    name = models.CharField("Name", max_length=255)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "City"
        verbose_name_plural = "Cities"

        unique_together = (
            "name",
            "country",
        )

    def __str__(self):
        return self.name


class IP(models.Model):
    address = models.CharField("IP address", max_length=255, unique=True)
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "IP"
        verbose_name_plural = "IPs"

    def __str__(self):
        return self.address


class UserAgent(models.Model):
    name = models.CharField("Name", max_length=1024, unique=True)

    class Meta:
        verbose_name = "User Agent"
        verbose_name_plural = "User Agents"

    def __str__(self):
        return self.name


class Domain(models.Model):
    name = models.CharField("Name", max_length=1024, unique=True)

    def __str__(self):
        return self.name


class Resource(models.Model):
    name = models.CharField("Name", max_length=1024, unique=True)

    def __str__(self):
        return self.name


class Referrer(models.Model):
    name = models.CharField("Name", max_length=1024, unique=True)

    def __str__(self):
        return self.name


class Method(models.Model):
    name = models.CharField("Name", max_length=1024, unique=True)

    def __str__(self):
        return self.name


class Protocol(models.Model):
    name = models.CharField("Name", max_length=1024, unique=True)

    def __str__(self):
        return self.name


class Request(models.Model):
    ip = models.ForeignKey(IP, on_delete=models.CASCADE)
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    user_agent = models.ForeignKey(UserAgent, on_delete=models.CASCADE)
    referrer = models.ForeignKey(Referrer, on_delete=models.CASCADE)
    method = models.ForeignKey(Method, on_delete=models.CASCADE)
    protocol = models.ForeignKey(Protocol, on_delete=models.CASCADE)
    posted_date = models.DateTimeField("Datetime")

    def __str__(self):
        return "%s - %s %s" % (self.ip, self.domain, self.resource)
