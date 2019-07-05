$(function() {
    function show_route_fields() {
        if ($('input[name=route]:checked').val() == 'order_system') {
            $('.order_system').removeClass('hide');
        } else {
            $('.order_system').addClass('hide');
        }
    }

    $("input[name=route]").on('click', function () {
        show_route_fields();
    });

    show_route_fields();
});

