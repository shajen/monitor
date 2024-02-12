$(document).ready(onReady);

function onReady() {
    Highcharts.setOptions({
        global: {
            useUTC: false
        }
    });

    $("#input_datetime_begin").change(function () {
        $("#input_last_type").val("");
        $("#input_last_count").val("");
    });
    $("#input_datetime_end").change(function () {
        $("#input_last_type").val("");
        $("#input_last_count").val("");
    });
    $("#input_last_type").change(function () {
        $("#input_datetime_begin").val("");
        $("#input_datetime_end").val("");
    });
    $("#input_last_count").change(function () {
        $("#input_datetime_begin").val("");
        $("#input_datetime_end").val("");
    });
    $("#graphs_form").submit(function (e) {
        e.preventDefault();
        loadPlot();
    });
    loadPlot();
}

function loadPlot() {
    $('#chart').hide();
    $('#loading').show();
    let old_params = new URLSearchParams(window.location.search);
    let new_params = {
        datetime_begin: $("#input_datetime_begin").val(),
        datetime_end: $("#input_datetime_end").val(),
        last_count: $("#input_last_count").val(),
        last_type: $("#input_last_type").val(),
        aggregation_time: $("#input_aggregation_time").val(),
        'sensor_id': old_params.get('sensor_id'),
        'sensor_type_id': old_params.get('sensor_type_id'),
        'group_id': old_params.get('group_id'),
    };
    if ($("#input_min_max").is(':checked')) {
        new_params['min_max'] = '';
    }
    window.history.pushState(null, null, window.location.pathname + "?" + $.param(new_params));
    new_params['format'] = 'json';
    $.getJSON(window.location.pathname, new_params, function (json) { renderPlot(json) });
}

function renderPlot(data) {
    $('#loading').hide();
    $('#chart').show();
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
