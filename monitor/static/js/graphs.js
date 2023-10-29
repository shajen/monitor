$(document).ready(onReady);

function onReady() {
    Highcharts.setOptions({
        global: {
            useUTC: false
        }
    });

    $("#input_datetime_begin").change(function () {
        $("#input_last_hours").val("");
    });
    $("#input_datetime_end").change(function () {
        $("#input_last_hours").val("");
    });
    $("#input_last_hours").change(function () {
        $("#input_datetime_begin").val("");
        $("#input_datetime_end").val("");
    });
    loadPlot();
}

function loadPlot() {
    const url = window.location.href + "&format=json";
    $.getJSON(url, function (json) { renderPlot(json) });
}

function renderPlot(data) {
    const is_single_sensor = data.sensors.length == 1;
    let series = [];
    let units = new Set();
    for (let i = 0; i < data.sensors.length; i++) {
        const sensor = data.sensors[i];
        if (sensor.mean_data) {
            mean_series = {
                name: sensor.name,
                data: sensor.mean_data,
                type: 'line',
                zIndex: 1,
                marker: {
                    fillColor: 'white',
                    lineWidth: 2,
                    lineColor: Highcharts.getOptions().colors[i]
                },
                tooltip: {
                    valueDecimals: 2,
                    valueSuffix: sensor.unit,
                }
            }
            series.push(mean_series);
            units.add(sensor.unit);

            if (sensor.min_max_data) {
                min_max_series = {
                    name: 'min max ' + sensor.name,
                    data: sensor.min_max_data,
                    type: 'arearange',
                    lineWidth: 0,
                    linkedTo: ':previous',
                    color: Highcharts.getOptions().colors[i],
                    fillOpacity: 0.3,
                    zIndex: 0,
                    marker: { enabled: false },
                    tooltip: {
                        valueDecimals: 2,
                        valueSuffix: sensor.unit
                    }
                }
                series.push(min_max_series);
            }
        }
    }
    let labels_style = { fontWeight: 'bold', fontSize: '13px' }
    let tooltip_style = { fontSize: '18px' }
    const common_unit = units.size == 1 ? [...units][0] : "";

    $('#chart').highcharts({
        chart: {
            type: 'container',
            zoomType: 'x'
        },
        title: { text: null },
        legend: {
            align: 'right',
            verticalAlign: 'top',
            y: 50,
            floating: true,
            borderWidth: 0
        },
        tooltip: {
            crosshairs: false,
            dateTimeLabelFormats: {
                second: '%Y-%m-%d %H:%M:%S',
                minute: '%Y-%m-%d %H:%M',
                hour: '%Y-%m-%d %H:%M',
                day: '%Y-%m-%d',
                week: '%Y-%m-%d',
                month: '%Y-%m',
                year: '%Y'
            },
            headerFormat: '{point.key}<br/>',
            style: tooltip_style,
            shared: is_single_sensor
        },
        xAxis: {
            type: 'datetime',
            dateTimeLabelFormats: {
                second: '%Y-%m-%d %H:%M:%S',
                minute: '%H:%M',
                hour: '%H:%M',
                day: '%Y-%m-%d',
                week: '%Y-%m-%d',
                month: '%Y-%m',
                year: '%Y'
            },
            labels: { style: labels_style },
            title: { text: 'Date', style: labels_style },
        },
        yAxis: {
            labels: { style: labels_style, format: "{value} " + common_unit },
            title: { text: data.name, style: labels_style }
        },
        series: series,
    });
}
