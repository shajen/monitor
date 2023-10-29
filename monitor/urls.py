import debug_toolbar
from django.urls import include, re_path
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.views.static import serve
from django.views.generic.base import TemplateView
from django.conf.urls.static import static

import graphs.views
import logs.views
import sdr.views

sdr_patterns = [
    re_path(r"^spectrograms/?$", sdr.views.spectrograms, name="sdr_spectrograms"),
    re_path(r"^spectrogram/(?P<spectrogram_id>[0-9]+)/?$", sdr.views.spectrogram, name="sdr_spectrogram"),
    re_path(r"^spectrogram/(?P<spectrogram_id>[0-9]+)/data/?$", sdr.views.spectrogram_data, name="sdr_spectrogram_data"),
    re_path(r"^transmissions/?$", sdr.views.transmissions, name="sdr_transmissions"),
    re_path(r"^transmission/(?P<transmission_id>[0-9]+)/?$", sdr.views.transmission, name="sdr_transmission"),
    re_path(r"^transmission/(?P<transmission_id>[0-9]+)/data/?$", sdr.views.transmission_data, name="sdr_transmission_data"),
    re_path(r"^group/add/?$", sdr.views.add_group, name="sdr_add_group"),
    re_path(r"^group/delete/(?P<group_id>[0-9]+)/?$", sdr.views.delete_group, name="sdr_delete_group"),
    re_path(r"^groups/?$", sdr.views.groups, name="sdr_groups"),
    re_path(r"^config/?$", sdr.views.config, name="sdr_config"),
]

urlpatterns = (
    [
        re_path(r"^admin/login/?$", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
        re_path(r"^admin/", admin.site.urls),
        re_path(r"^static/(?P<path>.*)$", serve, {"document_root": settings.STATIC_ROOT}),
        re_path(r"^$", TemplateView.as_view(template_name="index.html"), name="index"),
        re_path(r"^api/temp/add/?$", graphs.views.temperature_measurement_add),
        re_path(r"^graphs/?$", graphs.views.graphs, name="graphs"),
        re_path(r"^logs/?$", logs.views.logs, name="logs"),
        re_path(r"^sdr/", include(sdr_patterns)),
        re_path(r"^__debug__/", include(debug_toolbar.urls)),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)
