from django.contrib.admin.views.decorators import staff_member_required as login_required
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import permission_required
from logs.models import *
from monitor.views import *


@require_http_methods(["GET"])
@login_required()
@permission_required("logs.view_request", raise_exception=True)
def logs(request):
    order_by = request.GET.get("order_by", "-posted_date")
    requests = Request.objects.order_by(order_by).select_related("resource", "user_agent", "referrer", "ip__city__country", "ip__provider")
    (requests, additional_data) = filter_data(
        request,
        requests,
        [
            ("domain", "domain__name", "string", -1),
            ("resource", "resource__name", "string", -1),
            ("ip", "ip__address", "string", -1),
            ("city", "ip__city__name", "string", -1),
            ("country", "ip__city__country__name", "string", -1),
            ("provider", "ip__provider__name", "string", -1),
            ("user_agent", "user_agent__name", "string", -1),
        ],
    )
    return page_response(request, "logs.html", requests, order_by, additional_data=additional_data, objects_per_page=1000)
