$(function() {
    $('#id_address_template').on('change', function() {
        var select = $(this);

        $.ajax({
            url: select.data('url') + select.val(),
            type: 'get',
            success: function (data) {
                $.each(['post_code', 'contact_name', 'address_line_1', 'address_line_2', 'contact_number', 'id_number'], function(index, value) {
                    $('#id_' + value).val(data[value]);
                })
                if ($('#id_province').length > 0) {
                    $('#id_province').val(data.province);
                    $('#id_city, #id_district').find('option:not(:first)').remove();
                    $.ajax({
                        url: $('#id_province').data('lookup-url') + data.province,
                        type: 'get',
                        success: function (data2) {
                            $.each(data2, function(index, value) {
                                $('#id_city').append($('<option>', {value: value, text: value}));

                            });
                            $('#id_city').val(data.city);
                        }
                    });
                    $.ajax({
                        url: $('#id_city').data('lookup-url') + data.province + '/' + data.city,
                        type: 'get',
                        success: function (data2) {
                            $.each(data2, function(index, value) {
                                $('#id_district').append($('<option>', {value: value, text: value}));
                            });
                            $('#id_district').val(data.district);
                            if ($('#id_district').val()) {
                                $('#div_id_district2').addClass('hidden');
                            } else {
                                $('#div_id_district2').removeClass('hidden');
                                $('#id_district2').val(data.district);
                            }
                        }
                    });
                } else {
                    $('#id_city').val(data.city);
                }
            }
        });
    });
});