$(function() {
    $('#id_province, #id_city').on('change', function() {
        var select = $(this);
        $(select.data('children')).find('option:not(:first)').remove();
        $('#id_district2').val('');
        $('#div_id_district2').removeClass('hidden');

        var url = select.val() + '/';
        if (select.data('parent')) {
            url = $(select.data('parent')).val() + '/' + url;
        }

        $.ajax({
            url: select.data('lookup-url') + url,
            type: 'get',
            success: function (data) {
                $.each(data, function(index, value) {
                    $(select.data('target')).append($('<option>', {value: value, text: value}));
                });
            }
        });
    });

    $('#id_district').on('change', function() {
        if($(this).val()) {
            $('#id_district2').val('');
            $('#div_id_district2').addClass('hidden');
        } else {
            $('#div_id_district2').removeClass('hidden');
        }
    });
});
