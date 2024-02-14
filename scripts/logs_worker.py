#!/usr/bin/python3

from django.db.models import Max
from django.utils.timezone import localtime, make_aware
from logs.models import *
from monitor.settings import IP_GEOLOCATION_API_KEY
import logs.models
import sys
import re
import datetime
import urllib.parse
import urllib.request
import json
import logging
import shlex
import ipaddress


def parse(logger, line):
    line = re.sub(r"[\[\]]", "", line)
    data = shlex.split(line)
    return {
        "domain": data[0],
        "ip": data[1],
        "datetime": localtime(datetime.datetime.strptime(data[4] + " " + data[5], "%d/%b/%Y:%X %z")),
        "request": data[6],
        "status_code": data[7],
        "referrer": data[9],
        "user_agent": data[10],
    }


def get_ip(logger, ip):
    try:
        ip = IP.objects.get(address=ip)
        return ip
    except logs.models.IP.DoesNotExist:
        try:
            page = urllib.request.urlopen("https://api.ipgeolocation.io/ipgeo?apiKey=%s&ip=%s" % (IP_GEOLOCATION_API_KEY, ip))
            data = json.loads(page.read().decode("utf-8"))

            country, _ = Country.objects.get_or_create(name=data["country_name"])
            city, _ = City.objects.get_or_create(name=data["city"], country=country)
            provider, _ = Provider.objects.get_or_create(name=data["organization"])
            ip, _ = IP.objects.get_or_create(address=ip, city=city, provider=provider)
            logger.debug("+%s" % ip)
            return ip
        except urllib.error.HTTPError as e:
            logger.warning("Can not get IP details: %s, %s" % (ip, e))
            country, _ = Country.objects.get_or_create(name="")
            city, _ = City.objects.get_or_create(name="", country=country)
            provider, _ = Provider.objects.get_or_create(name="")
            ip, _ = IP.objects.get_or_create(address=ip, city=city, provider=provider)
            logger.debug("+%s" % ip)
            return ip


def run(*args):
    logger = logging.getLogger("logs")
    logger.setLevel(logging.INFO)
    latest_date = Request.objects.aggregate(Max("posted_date"))["posted_date__max"]
    latest_date = localtime(latest_date)
    logger.info("latest log date: %s" % latest_date.strftime("%Y-%m-%d %H:%M:%S"))
    processed = 0
    skipped = 0
    for line in sys.stdin:
        data = parse(logger, line)
        try:
            if latest_date < data["datetime"]:
                if ipaddress.ip_address(data["ip"]).is_private:
                    skipped += 1
                    continue
                try:
                    [method, resource, protocol] = data["request"].split(" ")
                except ValueError:
                    [method, resource, protocol] = ["", data["request"], ""]
                domain, _ = Domain.objects.get_or_create(name=data["domain"])
                ip = get_ip(logger, data["ip"])
                method, _ = Method.objects.get_or_create(name=method)
                protocol, _ = Protocol.objects.get_or_create(name=protocol)
                referrer, _ = Referrer.objects.get_or_create(name=data["referrer"])
                resource, _ = Resource.objects.get_or_create(name=resource)
                user_agent, _ = UserAgent.objects.get_or_create(name=data["user_agent"])
                processed += 1
                Request.objects.get_or_create(
                    domain=domain,
                    ip=ip,
                    method=method,
                    posted_date=data["datetime"],
                    protocol=protocol,
                    referrer=referrer,
                    resource=resource,
                    user_agent=user_agent,
                )
                logger.debug("+%s" % line.strip())
            else:
                skipped += 1
        except Exception as e:
            logger.error("Error, can not parse line: %s" % data)
            logger.exception(e)
    logger.info("processed logs: %d/%d" % (processed, processed + skipped))
