const count_row = $('.tech_drv_row').length;
const csrf = $('input[name="csrfmiddlewaretoken"]').val();
const pathname = window.location.pathname


for (let i=1;i<=count_row;i++) {
    const io_drv = '#io_drv_'+i;
    const select_drv = '#select_drv_'+i;
    const io_drv_val = $(io_drv).val();
        $(select_drv+' > option[value="'+io_drv_val+'"]').prop('selected', true);

    $('.row_'+i).click(function () {
        if ($('#inp_'+i).is(':checked')){
	        $('#inp_'+i).prop('checked', false);
        } else {
	        $('#inp_'+i).prop('checked', true);
        }
        sent(i);

    })
    $('#select_drv_'+i).change(function () {
        sent(i)
    });
}


function sent(i) {
        let id_drv = $('#select_drv_'+i).val();
        let status = $('#inp_'+i).is(':checked');
        let tech = $('#id_tech_drv_'+i).val()

        $.ajax({
        type: 'POST',
        mode: 'same-origin',
        url: pathname,
        data:{
            csrfmiddlewaretoken: csrf,
                id_drv: id_drv,
                status: status,
                tech: tech
            }
        })
}