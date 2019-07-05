$(function() {
    $('#track-form').on('submit',function(e){
        $('.se-pre-con').show();
        var $form = $(this);
        if ($form.data('submitted') === true) {
            e.preventDefault();
        } else {
            $form.data('submitted', true);
            $('.container').hide();
        }
    });
});

$(window).load(function() {
    $(".se-pre-con").fadeOut("slow");
    $(".container").fadeIn("slow");
});
