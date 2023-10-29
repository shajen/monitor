$(document).ready(function () {
    const offsetTop = $("#scrollable-main-image").offset()['top'];
    $(document).scroll(function () {
        if (offsetTop < window.pageYOffset) {
            $("#fixed-top-image").css('padding-top', $("nav.navbar").outerHeight());
            $("#fixed-top-image").css('display', 'block');
            $("#scrollable-top-image").scrollLeft($("#scrollable-main-image").scrollLeft());
        } else {
            $("#fixed-top-image").css('display', 'none');
        }
    });
    $("#scrollable-main-image").scroll(function () {
        $("#scrollable-top-image").scrollLeft($("#scrollable-main-image").scrollLeft());
    });
    if ($('#spectrogram').length) {
        $.ajax({
            url: $.url('path') + "/data?format=raw",
            type: "GET",
            processData: false,
            xhrFields: {
                responseType: 'arraybuffer'
            },
            success: function (data) {
                var offset = 0;
                var x_size = new Uint32Array(data.slice(offset, offset += 4));
                x_size = Number(x_size[0]);
                var x_labels = new Uint32Array(data.slice(offset, offset += 4 * x_size));


                var y_size = new Uint32Array(data.slice(offset, offset += 4));
                y_size = Number(y_size[0]);
                var y_labels = new BigUint64Array(data.slice(offset, offset += 8 * y_size));

                data = new Int8Array(data.slice(offset, offset += x_size * y_size));
                spectrogramData = []
                y_labels.forEach(function (y, y_index) {
                    x_labels.forEach(function (x, x_index) {
                        spectrogramData.push([Number(x), Number(y) / 1000, Number(data[y_index * x_size + x_index])]);
                    });
                });
                var x_min = Number(x_labels[0]);
                var x_max = Number(x_labels.at(-1));
                var y_min = Number(y_labels[0]) / 1000;
                var y_max = Number(y_labels.at(-1)) / 1000;

                console.log(x_size);
                console.log(y_size);
                console.log(x_min, x_max);
                console.log(y_min, y_max);
                buildSpectrogram(spectrogramData, y_min, y_max, x_min, x_max);
            }
        });
    }
});

function buildSpectrogram(data, y_min, y_max, x_min, x_max) {
    console.log('buildSpectrogram', y_min, y_max, x_min, x_max);
    Highcharts.chart('spectrogram', {
        chart: {
            type: 'heatmap'
        },
        boost: {
            useGPUTranslations: true
        },
        title: {
            text: null,
        },
        xAxis: {
            title: {
                text: 'Frequnecy'
            },
            min: x_min,
            max: x_max,
            labels: {
                align: 'left',
                x: 5,
                y: 14,
                format: '{value}'
            },
            showLastLabel: true,
            tickLength: 16
        },
        yAxis: {
            title: {
                text: 'Date'
            },
            labels: {
                format: '{value}'
            },
            minPadding: 0,
            maxPadding: 0,
            startOnTick: false,
            endOnTick: false,
            min: y_min,
            max: y_max,
            reversed: true
        },

        colorAxis: {
            stops: [
                [0, '#3060cf'],
                [0.5, '#fffbbc'],
                [0.9, '#c4463a'],
                [1, '#c4463a']
            ],
            min: -50,
            max: 50,
            startOnTick: false,
            endOnTick: false,
            labels: {
                format: '{value} dBm'
            }
        },

        series: [{
            boostThreshold: 100,
            borderWidth: 0,
            nullColor: '#EFEFEF',
            colsize: 1000,
            tooltip: {
                headerFormat: 'Power<br/>',
                pointFormat: '<b>{point.value} dBm</b>, {point.x} Hz, {point.y}'
            },
            turboThreshold: Number.MAX_VALUE,
            data: data,
        }]
    })
}