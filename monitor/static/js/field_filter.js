$(document).ready(updateFieldsFilter);

function updateField(field) {
    var count = 0;
    $("input[id^=input_][id*='" + field + "']").each(function () {
        if ($(this).is(':checked')) {
            count += 1;
        }
    });
    $("#" + field + "_list_select_count").text(count);
}

function onChange(id) {
    updateField($("#" + id).attr('field-id'));
}

function updateFieldsFilter() {
    $.datetimepicker.setLocale('pl');
    params = new URLSearchParams(window.location.search);
    for (p of params) {
        field = $("#input_" + p[0]);
        field.val(p[1]);
        field.prop("checked", true);
    }
    $("input[id^=input_]").each(function () {
        updateField($(this).attr('field-id'));
        if (this.id.includes('input_datetime_')) {
            $(this).datetimepicker({ format: 'Y-m-d H:i', dayOfWeekStart: 1 });
        }
        else if (this.id.includes('input_date_')) {
            $(this).datetimepicker({ format: 'Y-m-d', dayOfWeekStart: 1, timepicker: false });
        }
    });
    $("input[id^=input_][id*='_select_']").change(function () {
        onChange(this.id);
    });
    $("input[id^=input_][id*='_range_']").change(function () {
        onChange(this.id);
    });
}
