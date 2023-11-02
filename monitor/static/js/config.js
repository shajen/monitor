var scanners = {};
var devices = {};

$(document).ready(function () {
    if (window.location.protocol == 'http:') {
        connect('ws://' + window.location.hostname + ':' + $('#config').attr('mqtt_port'));
    }
    connect('wss://' + window.location.hostname + ':' + $('#config').attr('mqtt_port'));

    $("#expert_mode_checkbox").change(function () {
        if (this.checked) {
            $("#expert_mode_section").show();
        }
        else {
            $("#expert_mode_section").hide();
        }
    });
});

function connect(url) {
    let client = mqtt.connect(url, { username: $('#config').attr('mqtt_user'), password: $('#config').attr('mqtt_password') });
    client.on("message", function (topic, message) {
        let values = topic.split("/");
        let name = values[1];
        let id = values[2];
        if (name == 'status') {
            if (!(id in scanners)) {
                addScanner(id);
                let data = jQuery.parseJSON(new TextDecoder().decode(message))
                scanners[id] = { "config": data["config"], devices: [] };
                for (const [key, value] of Object.entries(data["devices"]).sort((a, b) => a[0].localeCompare(b[0]))) {
                    scanners[id]["devices"].push(key);
                    devices[key] = value;
                };
            }
        }
        else if (name == "config" && values[3] == "success") {
            $("#save").html("Save");
            $('#save_success').modal('show');
        }
    });

    client.on("connect", function () {
        console.log("connected to " + url);
        onConnect(client);
    });
    client.on("error", function () {
        client.end();
    });
    client.stream.on('error', function () {
        client.end();
    });
}

function onConnect(client) {
    client.subscribe("sdr/status/+");
    client.subscribe("sdr/config/+/success");
    client.publish("sdr/list");
    $("#save").click(function () {
        for (const [scanner_id, value] of Object.entries(scanners)) {
            let ranges = [];
            for (const device_id of scanners[scanner_id]['devices']) {
                let gains = {};
                for (const gain of devices[device_id]['gains']) {
                    gains[gain['name']] = gain['value']
                }
                let range = { "device_enabled": devices[device_id]["enabled"], "device_serial": device_id, "device_gains": gains, "ranges": devices[device_id]["ranges"] };
                ranges.push(range);
            }
            let config = scanners[scanner_id]['config'];
            config['scanned_frequencies'] = ranges;
            client.publish("sdr/config/" + scanner_id, JSON.stringify(config));
        }
        $("#save").prop("disabled", true);
        $("#save").html("<span class=\"spinner-border spinner-border-sm\" aria-hidden=\"true\"></span><span role=\"status\">Loading...</span>");
    });
}

function parseValue(value, type) {
    if (type == 'string') {
        return value;
    }
    else if (type == 'float') {
        return parseFloat(value);
    }
    else {
        return parseInt(value);
    }
}

function addScanner(id) {
    let d = document.createElement("div");
    $(d).addClass('form-check');

    let i = document.createElement("input");
    $(i).addClass('form-check-input');
    $(i).prop("type", "radio");
    $(i).prop("name", "scanner_selector");
    $(i).prop("value", id);
    $(i).attr("id", id);
    $(i).click(function () {
        selectScanner($(this).val());
    });

    let l = document.createElement("label");
    $(l).addClass("form-check-label");
    $(l).append("#" + ($("#scanner_selector").children().length + 1));
    $(l).attr("for", id);

    $(d).append(i);
    $(d).append(l);

    $("#scanner_selector").append(d);
}

function selectScanner(id) {
    updateInput('#transmission_max_noise_time_ms', id, ['recording', 'max_noise_time_ms']);
    updateInput("#transmission_min_time_ms", id, ['recording', 'min_time_ms']);
    updateInput("#transmission_sample_rate", id, ['recording', 'min_sample_rate']);
    updateInput("#transmission_group_size", id, ['detection', 'frequency_grouping_size']);
    updateInput("#scanning_time_ms", id, ['detection', 'frequency_range_scanning_time_ms']);
    updateInput("#noise_detection_margin", id, ['detection', 'noise_detection_margin']);
    updateInput("#noise_mearing_time_seconds", id, ['detection', 'noise_learning_time_seconds']);
    updateInput("#torn_transmission_learning_time_seconds", id, ['detection', 'torn_transmission_learning_time_seconds']);
    updateInput("#logs_directory", id, ['output', 'logs'], 'string');
    updateInput("#file_log_level", id, ['output', 'file_log_level'], 'string');
    updateInput("#console_log_level", id, ['output', 'console_log_level'], 'string');
    updateInput("#cores_limit", id, ['cores']);
    updateInput("#memory_limit", id, ['memory_limit_mb']);

    $("#device_selector").empty();
    $("#ignored_frequencies").find("tr:gt(0)").remove();
    scanners[id]['devices'].forEach(function (device) {
        addDevice(device);
    });
    scanners[id]['config']['ignored_frequencies'] = scanners[id]['config']['ignored_frequencies'].sort((a, b) => a['frequency'] > b['frequency']);
    scanners[id]['config']['ignored_frequencies'].forEach(function (frequency) {
        addIgnoredFrequency(id, frequency['frequency'], frequency['bandwidth']);
    });
    $("#new_ignored_frequency").prop("disabled", false);
    $("#new_ignored_frequency").unbind("click");
    $("#new_ignored_frequency").click(function () {
        addIgnoredFrequency(id, 0, 0);
        scanners[id]['config']['ignored_frequencies'].push({ 'frequency': 0, 'bandwidth': 0 });
        $("#save").prop("disabled", false);
    });
    $("#device_enabled").prop("disabled", true);
    $("#new_scanned_frequency").prop("disabled", true);
}

function updateInput(element, id, keys, type = 'integer') {
    if (2 <= keys.length) { $(element).val(scanners[id]['config'][keys[0]][keys[1]]); }
    else { $(element).val(scanners[id]['config'][keys[0]]); }
    $(element).prop("disabled", false);
    $(element).change(function () {
        let value = parseValue($(this).val(), type)
        if (2 <= keys.length) { scanners[id]['config'][keys[0]][keys[1]] = value; }
        else { scanners[id]['config'][keys[0]] = value; }
        $("#save").prop("disabled", false);
    });
}

function addDevice(id) {
    let d = document.createElement("div");
    $(d).addClass('form-check');

    let i = document.createElement("input");
    $(i).addClass('form-check-input');
    $(i).prop("type", "radio");
    $(i).prop("name", "device_selector");
    $(i).prop("value", id);
    $(i).attr("id", id);
    $(i).click(function () {
        selectDevice($(this).val());
    });

    let l = document.createElement("label");
    $(l).addClass("form-check-label");
    $(l).append(devices[id]["model"] + " - " + id);
    $(l).attr("for", id);

    $(d).append(i);
    $(d).append(l);

    $("#device_selector").append(d);
    $("#scanned_frequencies").find("tr:gt(0)").remove();
    $("#gains").find("tr:gt(0)").remove();
}

function addIgnoredFrequency(id, frequency, bandwidth) {
    let tr = document.createElement("tr");
    $(tr).append(createInput(frequency, function (value) {
        let index = Array.prototype.indexOf.call($(tr).parent().children(), tr) - 1;
        scanners[id]['config']['ignored_frequencies'][index]['frequency'] = value;
    }));
    $(tr).append(createInput(bandwidth, function (value) {
        let index = Array.prototype.indexOf.call($(tr).parent().children(), tr) - 1;
        scanners[id]['config']['ignored_frequencies'][index]['bandwidth'] = value;
    }));
    $(tr).append(createButton("Delete", function () {
        let index = Array.prototype.indexOf.call($(tr).parent().children(), tr) - 1;
        scanners[id]['config']['ignored_frequencies'].splice(index, 1);
        tr.remove();
        $("#save").prop("disabled", false);
    }));
    $("#ignored_frequencies").append(tr);
}

function selectDevice(id) {
    $("#device_enabled").prop("checked", devices[id]['enabled']);
    $("#device_enabled").prop("disabled", false);
    $("#device_enabled").unbind("click");
    $("#device_enabled").click(function () {
        devices[id]['enabled'] = $(this).is(':checked');
        $("#save").prop("disabled", false);
    });
    $("#scanned_frequencies").find("tr:gt(0)").remove();
    $("#gains").find("tr:gt(0)").remove();
    devices[id]['ranges'] = devices[id]['ranges'].sort((a, b) => a['start'] > b['start']);
    devices[id]['ranges'].forEach(function (frequency) {
        addScannedFrequency(id, frequency['start'], frequency['stop'], frequency['sample_rate']);
    });
    devices[id]['gains'] = devices[id]['gains'].sort((a, b) => a['name'].localeCompare(b['name']));
    devices[id]['gains'].forEach(function (gain) {
        addGain(id, gain['name'], gain['value'], gain['min'], gain['max'], gain['step']);
    });
    $("#new_scanned_frequency").prop("disabled", false);
    $("#new_scanned_frequency").unbind("click");
    $("#new_scanned_frequency").click(function () {
        addScannedFrequency(id, 0, 0, devices[id]['default_sample_rate']);
        devices[id]['ranges'].push({ 'start': 0, 'stop': 0, 'sample_rate': devices[id]['default_sample_rate'] });
        $("#save").prop("disabled", false);
    });
}

function addScannedFrequency(id, start, stop, sample_rate) {
    let tr = document.createElement("tr");
    $(tr).append(createInput(start, function (value) {
        let index = Array.prototype.indexOf.call($(tr).parent().children(), tr) - 1;
        devices[id]['ranges'][index]['start'] = value;
    }));
    $(tr).append(createInput(stop, function (value) {
        let index = Array.prototype.indexOf.call($(tr).parent().children(), tr) - 1;
        devices[id]['ranges'][index]['stop'] = value;
    }));
    $(tr).append(createInput(sample_rate, function (value) {
        let index = Array.prototype.indexOf.call($(tr).parent().children(), tr) - 1;
        devices[id]['ranges'][index]['sample_rate'] = value;
    }));
    $(tr).append(createButton("Delete", function () {
        let index = Array.prototype.indexOf.call($(tr).parent().children(), tr) - 1;
        devices[id]['ranges'].splice(index, 1);
        tr.remove();
        $("#save").prop("disabled", false);
    }));
    $("#scanned_frequencies").append(tr);
}

function addGain(id, name, value, min, max, step) {
    let tr = document.createElement("tr");
    $(tr).append(createLabel(name));
    $(tr).append(createInput(value, function (value) {
        let index = Array.prototype.indexOf.call($(tr).parent().children(), tr) - 1;
        devices[id]['gains'][index]['value'] = value;
    }, 'float'));
    $(tr).append(createLabel(min));
    $(tr).append(createLabel(max));
    $(tr).append(createLabel(step));
    $("#gains").append(tr);
}

function createLabel(value) {
    let td = document.createElement("td");
    td.append(value);
    return td;
}

function createInput(value, callback, type = 'integer') {
    let td = document.createElement("td");
    let i = document.createElement("input");
    $(i).addClass("form-control");
    $(i).val(value);
    $(i).change(function () {
        callback(parseValue($(this).val(), type));
        $("#save").prop("disabled", false);
    });
    td.append(i);
    return td;
}

function createButton(value, callback) {
    let td = document.createElement("td");
    let b = document.createElement("button");
    $(b).addClass("btn");
    $(b).addClass("btn-danger");
    $(b).attr("type", "button");
    $(b).append(value);
    $(b).click(callback);
    td.append(b)
    return td;
}
