const count_row = $('.tech_drv_row').length;
const csrf = $('input[name="csrfmiddlewaretoken"]').val();
const pathname = window.location.pathname


for (let i=1;i<=count_row;i++) {
    const io_drv = '#io_drv_'+i;
    const select_drv = '#select_drv_'+i;
    const io_drv_val = $(io_drv).val();

    if ($('#inp_'+i).is(':checked')){
        $(select_drv+' > option[value="'+io_drv_val+'"]').prop('selected', true);
    }

    $('.row_'+i).click(function () {
        if ($('#inp_'+i).is(':checked')){
	        $('#inp_'+i).prop('checked', false);
        } else {
	        $('#inp_'+i).prop('checked', true);
        }
    })
}

const notice = $('#notice_stat');
notice.hide()
if (notice.attr('status')){
    notice.show()
    setTimeout(function() { notice.hide(); }, 2000)
}

