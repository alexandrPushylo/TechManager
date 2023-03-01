const cw_date = $('.io_current_day');
cw_date.change(function () {
    location.href = '/supply_app/'+this.value;
})

$('.app_description').each(function () {
    this.style.height = ""+(this.scrollHeight)+"px";
});

const csrf = $('input[name="csrfmiddlewaretoken"]').val();
const pathname = window.location.pathname;

$('.btn_panel').click(function () {
    if($('.foreman_panel').is(':hidden')){
            $('.foreman_panel').prop('hidden',false)
        }else {
            $('.foreman_panel').prop('hidden',true)
        }
    $.ajax({
        type: 'POST',
        mode: 'same-origin',
        url: pathname,
        data: {
            csrfmiddlewaretoken: csrf,
                panel: $('.foreman_panel').is(':hidden')
        }
    })
    return false
})