from django import template
import humanize

register = template.Library()


def append(str, unit, value, current_unit):
    if value == 0:
        return (str, unit)
    else:
        if str == "":
            return ("%d" % value, current_unit)
        else:
            return ("%s.%03d" % (str, value), unit)


def frequency(value, force_segment=None):
    try:
        value = int(value)
        if value == 0:
            return "0 Hz"
        (str, unit) = ("", "")
        (str, unit) = append(str, unit, value // 1000000000, "GHz")
        (str, unit) = append(str, unit, (value // 1000000) % 1000, "MHz")
        (str, unit) = append(str, unit, (value // 1000) % 1000, "kHz")
        (str, unit) = append(str, unit, value % 1000, "Hz")
        return "%s %s" % (str, unit)
    except:
        return value


def natural_size(value):
    return humanize.naturalsize(value)


def big_number(value):
    return humanize.intcomma(value).replace(",", " ")


register.filter("frequency", frequency)
register.filter("natural_size", natural_size)
register.filter("big_number", big_number)
