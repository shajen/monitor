from django.utils import timezone
from django.utils.timezone import make_aware
from monitor.settings import BASE_DIR
import sdr.templatetags.filters
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont
import numpy as np
import matplotlib.pyplot
import math
import OpenImageIO as oiio


class Drawer:
    def __init__(self, **kwargs):
        self.__frequency_labels_count = kwargs.get("frequency_labels_count", 10)
        self.__power_step = kwargs.get("power_step", 10)
        self.__seconds_step = kwargs.get("seconds_step", 60)
        self.__draw_frequency = kwargs.get("draw_frequency", True)
        self.__draw_power = kwargs.get("draw_power", True)
        self.__draw_time = kwargs.get("draw_time", True)
        self.__draw_data = kwargs.get("draw_data", True)
        self.__draw_bottom = kwargs.get("draw_bottom", False)
        self.__text_size = kwargs.get("text_size", 20)
        self.__text_stroke = kwargs.get("text_stroke", 2)
        self.__min_width = kwargs.get("min_width", 0)
        self.__background = "gray"
        self.__power_height = 50
        self.__frequency_height = 35
        self.__time_width = 100
        self.__line_width = 10
        self.__font = PIL.ImageFont.truetype(BASE_DIR + "/font.ttf", self.__text_size)
        self.__line_style = {"fill": "black", "width": 2}
        self.__text_size_style = {"stroke_width": self.__text_stroke, "font": self.__font}
        self.__text_style = {"fill": "black", "stroke_width": self.__text_stroke, "stroke_fill": "white", "font": self.__font}

    def __draw_frequency_labels(self, x_size, begin_frequency, end_frequency, y_offset, include_up, include_down):
        image = PIL.Image.new("RGB", (x_size, self.__frequency_height), self.__background)
        draw = PIL.ImageDraw.Draw(image)
        for x in range(1, self.__frequency_labels_count):
            step = (end_frequency - begin_frequency) // self.__frequency_labels_count
            step2 = image.width / self.__frequency_labels_count
            text = sdr.templatetags.filters.frequency(begin_frequency + x * step, 2)
            (l, t, r, b) = draw.textbbox([0, 0], text, **self.__text_size_style)
            (w, h) = (r - l, b - t)
            draw.text((x * step2 - w // 2, y_offset - h), text, **self.__text_style)
            if include_up:
                draw.line(((x * step2, y_offset - h - self.__line_width), (x * step2, y_offset - h)), **self.__line_style)
            if include_down:
                draw.line(((x * step2, y_offset), (x * step2, y_offset + self.__line_width)), **self.__line_style)
        return np.array(image).reshape(image.height, image.width, 3)

    def __draw_time_labels(self, y_size, y_offset, dates, zoom_out):
        image = PIL.Image.new("RGB", (self.__time_width, y_size + 2 * y_offset), self.__background)
        draw = PIL.ImageDraw.Draw(image)
        minimal_diff = 30
        x_offset = 4
        last_draw = -minimal_diff
        for i in range(1, len(dates)):
            d1 = dates[i - 1] // 1000
            d2 = dates[i] // 1000
            if d1 // self.__seconds_step != d2 // self.__seconds_step and minimal_diff <= i - last_draw:
                last_draw = i
                dt = make_aware(timezone.datetime.fromtimestamp(dates[i] / 1000))
                text = dt.strftime("%H:%M:%S")
                (l, t, r, b) = draw.textbbox([0, 0], text, **self.__text_size_style)
                (w, h) = (r - l, b - t)
                draw.text((x_offset, (i - h // 2 + y_offset) // zoom_out), text, **self.__text_style)
                draw.line(((x_offset + w, (i + y_offset) // zoom_out), (x_offset + w + self.__line_width, (i + y_offset) // zoom_out)), **self.__line_style)
        return np.array(image).reshape(image.height, image.width, 3)

    def __draw_power_labels(self, x_size, colors, data_min, data_max, text_on_top):
        image = PIL.Image.new("RGB", (x_size, self.__power_height), self.__background)
        draw = PIL.ImageDraw.Draw(image)
        size = image.width // (data_max - data_min + 1)
        for value in range(data_min, data_max + 1):
            index = value - data_min
            (l, t, r, b) = draw.textbbox([0, 0], str(value), **self.__text_size_style)
            (w, h) = (r - l, b - t)
            if (value - 1) // self.__power_step != value // self.__power_step:
                if text_on_top:
                    draw.text((index * size - w // 2 + size // 2, 0), str(value), **self.__text_style)
                else:
                    draw.text((index * size - w // 2 + size // 2, image.height - h), str(value), **self.__text_style)
            if text_on_top:
                draw.rectangle(((index * size, h), ((index + 1) * size, image.height)), fill=tuple(colors[index]))
            else:
                draw.rectangle(((index * size, 0), ((index + 1) * size, image.height - h)), fill=tuple(colors[index]))
        return np.array(image).reshape(image.height, image.width, 3)

    def append(self, image, data_left, data_right, y_offset):
        if data_right is None:
            return 0
        y_size = data_right.shape[0]
        for y in range(y_size):
            if data_left is None:
                image.write_scanline(y_offset + y, 0, data_right[y])
            else:
                image.write_scanline(y_offset + y, 0, np.concatenate((data_left[y + y_offset], data_right[y])))
        return y_size

    def draw_spectrogram(self, data, image_filename, x_size, y_size, begin_frequency, end_frequency, y_labels):
        data_min = int(data.min())
        data_max = int(data.max())
        cmap = matplotlib.pyplot.get_cmap("jet")
        factor = data_max - data_min + 1
        colors = np.array([np.array(cmap(i / factor, bytes=True)[:-1]).astype(np.uint8) for i in range(0, factor)])

        zoom = self.__min_width // x_size if (0 < self.__min_width and x_size < self.__min_width) else 1
        zoom_out = int(math.ceil(y_size / 65000)) if 65000 < y_size else 1
        if 1 < zoom_out:
            zoom = 1
        self.__seconds_step *= zoom_out
        (width, height) = (0, 0)
        if self.__draw_data or self.__draw_frequency or self.__draw_power:
            width += x_size * zoom
        if self.__draw_data or self.__draw_time:
            height += y_size * zoom // zoom_out
        if self.__draw_time:
            y_offset = 0
            if self.__draw_frequency:
                y_offset += self.__frequency_height
            if self.__draw_power:
                y_offset += self.__power_height
            width += self.__time_width
            time_data = self.__draw_time_labels(y_size * zoom // zoom_out, y_offset, y_labels, zoom_out)
        else:
            time_data = None
        if self.__draw_power:
            height += self.__power_height
            power_top_data = self.__draw_power_labels(x_size * zoom, colors, data_min, data_max, True)
            if self.__draw_bottom:
                height += self.__power_height
                power_bottom_data = self.__draw_power_labels(x_size * zoom, colors, data_min, data_max, False)
        else:
            power_top_data = None
            power_bottom_data = None
        if self.__draw_frequency:
            height += self.__frequency_height
            frequency_top_data = self.__draw_frequency_labels(x_size * zoom, begin_frequency, end_frequency, 22, False, True)
            if self.__draw_bottom:
                height += self.__frequency_height
                frequency_bottom_data = self.__draw_frequency_labels(x_size * zoom, begin_frequency, end_frequency, self.__frequency_height, True, False)
        else:
            frequency_top_data = None
            frequency_bottom_data = None

        image = oiio.ImageOutput.create(image_filename)
        spec = oiio.ImageSpec(width, height, 3, "uint8")
        spec.attribute("compression", "jpeg:75")
        image.open(image_filename, spec)

        y_offset = 0
        y_offset += self.append(image, time_data, power_top_data, y_offset)
        y_offset += self.append(image, time_data, frequency_top_data, y_offset)
        for y in range(y_size - y_size % 2):
            if self.__draw_data:
                subdata = data[y : y + 1, :].reshape(-1, x_size) - data_min
                subimage = colors[subdata].reshape(-1, 3)
                if 1 < zoom:
                    subimage = np.repeat(subimage, zoom, axis=0)
                    subimage = np.tile(subimage, (zoom, 1, 1))
                if y % zoom_out == zoom_out - 1:
                    y_start = y_offset + y * zoom // zoom_out
                    y_stop = y_offset + (y + 1) * zoom // zoom_out
                    if time_data is None:
                        image.write_scanlines(y_start, y_stop, 0, subimage)
                    else:
                        image.write_scanlines(y_start, y_stop, 0, np.concatenate((time_data[y_offset + y // zoom_out], subimage)))
            elif time_data is not None:
                y_start = y_offset + y * zoom // zoom_out
                y_stop = y_offset + (y + 1) * zoom // zoom_out
                image.write_scanlines(y_start, y_stop, 0, time_data[y_offset + y // zoom_out])
        if time_data is not None or self.__draw_data:
            y_offset += y_size * zoom // zoom_out
        if self.__draw_bottom:
            y_offset += self.append(image, time_data, frequency_bottom_data, y_offset)
            y_offset += self.append(image, time_data, power_bottom_data, y_offset)
        image.close()
