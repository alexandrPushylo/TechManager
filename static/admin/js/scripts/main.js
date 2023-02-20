$('.app_description').each(function () {
    this.style.height = ""+(this.scrollHeight)+"px";
});

const cw_date = $('.io_current_day');
cw_date.change(function () {
    location.href = '/applications/'+this.value;
})

$('.div_td').click(function () {
    location.href = '/append_in_hos_tech/'+this.id;

})

const csrf = $('input[name="csrfmiddlewaretoken"]').val();
const pathname = window.location.pathname;

$('.btn_driver_panel').click(function () {
    if($('.driver_panel').is(':hidden')){
            $('.driver_panel').prop('hidden',false)
        }else {
            $('.driver_panel').prop('hidden',true)
        }
    $.ajax({
        type: 'POST',
        mode: 'same-origin',
        url: pathname,
        data: {
            csrfmiddlewaretoken: csrf,
                panel: $('.driver_panel').is(':hidden')
        }
    })
    return false
})

$('.driver_name_link').click(function () {
    if(this.id){
        location.href = '/personal_application/'+$('.io_current_day').val()+'/'+this.id;
    }

})