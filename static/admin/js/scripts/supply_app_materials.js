const cw_date = $('.io_current_day');
cw_date.change(function () {
    location.href = '/materials/'+this.value;
})

$('.app_description').each(function () {
    this.style.height = ""+(this.scrollHeight)+"px";
});

$('.app_description').on('input', function(){
	this.style.height = '1px';
	this.style.height = (this.scrollHeight + 6) + 'px';
});


const csrf = $('input[name="csrfmiddlewaretoken"]').val();
const pathname = window.location.pathname;

// const io_id_app_m = $('#io_id_app_m');
const btn_status_check = $('.btn_status_check');
btn_status_check.click(function () {
    sent()
})

function sent() {
        $.ajax({
        type: 'POST',
        mode: 'same-origin',
        url: pathname,
        data:{
            csrfmiddlewaretoken: csrf,
                status_checked: true
            },
        success: function() {
            window.location.reload();
            }
        })
}

