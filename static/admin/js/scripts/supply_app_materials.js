const cw_date = $('.io_current_day');
cw_date.change(function () {
    location.href = '/materials/'+this.value;
})

$('.app_description').each(function () {
    this.style.height = ""+(this.scrollHeight)+"px";
});

const csrf = $('input[name="csrfmiddlewaretoken"]').val();
const pathname = window.location.pathname;

$('.app_description').on('input', function () {
    const desc_id = this.id;
    $('#div'+desc_id).removeClass('border','border-success', 'border-2');
    $('#btn_save').val('Сохранить изменения');
    $('#btn_save').removeClass('btn-danger').addClass('btn-warning');
    $('#btn_ch_'+desc_id).val('Сохранить')
    $('#btn_ch_'+desc_id).removeClass('btn-outline-success').addClass('btn-warning');
    $('#labl_'+desc_id).text('Не сохранено');
});

$('.btn_print').click(function () {
    window.open(pathname.replace('materials','print'))

});


