const count_row = $('.tech_drv_row').length;


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
    })
}

const cw_date = $('.io_current_day');
cw_date.change(function () {
    location.href = '/technic_driver/'+this.value;
})

