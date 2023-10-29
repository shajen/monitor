from django.contrib import admin
from logs.models import *
from monitor.settings import FULL_MODE_ENABLED


class ProviderAdmin(admin.ModelAdmin):
    list_display = ("id", "name")

    search_fields = ["name"]


class CountryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")

    search_fields = ["name"]


class CityAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "country")

    search_fields = ["name"]


class DomainAdmin(admin.ModelAdmin):
    list_display = ("id", "name")

    search_fields = ["name"]


class IPAdmin(admin.ModelAdmin):
    list_display = ("id", "address", "get_country", "city")

    search_fields = ["address"]

    def get_country(self, obj):
        return obj.city.country

    get_country.admin_order_field = "city__country"
    get_country.short_description = "Country"


class MethodAdmin(admin.ModelAdmin):
    list_display = ("id", "name")

    search_fields = ["name"]


class ProtoctolAdmin(admin.ModelAdmin):
    list_display = ("id", "name")

    search_fields = ["name"]


class UserAgentAdmin(admin.ModelAdmin):
    list_display = ("id", "name")

    search_fields = ["name"]


class ResourceAdmin(admin.ModelAdmin):
    list_display = ("id", "name")

    search_fields = ["name"]


class ReferrerAdmin(admin.ModelAdmin):
    list_display = ("id", "name")

    search_fields = ["name"]


class RequestAdmin(admin.ModelAdmin):
    list_display = ("id", "ip", "domain", "resource", "user_agent", "method", "protocol", "posted_date")

    search_fields = ["resource"]


if FULL_MODE_ENABLED:
    admin.site.register(Provider, ProviderAdmin)
    admin.site.register(Country, CountryAdmin)
    admin.site.register(City, CityAdmin)
    admin.site.register(Domain, DomainAdmin)
    admin.site.register(IP, IPAdmin)
    admin.site.register(Method, MethodAdmin)
    admin.site.register(Protocol, ProtoctolAdmin)
    admin.site.register(UserAgent, UserAgentAdmin)
    admin.site.register(Resource, ResourceAdmin)
    admin.site.register(Referrer, ReferrerAdmin)
    admin.site.register(Request, RequestAdmin)
