console.log('fdf')
const count_vehicles = $('.input_tech').length;

for(let i=1;i<=count_vehicles;i++){
    let input_tech = '#input_tech_'+i;
    let input_driver = '#input_driver_'+i;
    let io_veh = '#io_vehicle_'+i;
    let io_drv = '#io_driver_'+i;
    let btn_reset = '#btn_reset_'+i;

    let curr_vehicle = $(input_tech);
    let curr_driver = $(input_driver);
    let curr_io_veh = $(io_veh);
    let curr_io_drv = $(io_drv);
    let curr_btn_rst = $(btn_reset);

    const v_tech = $(io_veh).val();
    const v_drv = $(io_drv).val();



    $(input_tech+'> option[value="'+ v_tech +'"]').prop('selected',true);
    $(input_driver +'> option[veh="'+ v_tech+'"]').attr('hidden',false);
    if(v_drv === ''){
        $(input_driver +" > option:checked").val('').text('---');
    }else {
        $(input_driver+'> option[value="'+ v_drv +'"]').prop('selected',true);
    }

    curr_btn_rst.click(function () {
        $(input_driver +'> option[value="'+ curr_io_drv.val() +'"]').first().prop('selected',true);
        $(input_tech +'> option[value="'+ curr_io_veh.val()+'"]').first().prop('selected',true);
        return false;
    });

    curr_vehicle.change(function () {
        $(input_driver +'> option').attr('hidden',true);
        $(input_driver +"> option[selected]").attr('hidden',true);
        const checked_tech = this.value;
        $(input_driver +'> option[veh="'+ checked_tech+'"]').attr('hidden',false);

        if ($(input_driver +" option[hidden!='hidden']").length < 2){
        $(input_driver +" option[hidden!='hidden']:last").prop('selected', true);
        }
        else {
            $(input_driver +" option[hidden!='hidden']:first").prop('selected', true);
        // $(input_driver +" > option:checked").val('').text('---');
        }



    });
}

$('.app_description').each(function () {
    this.style.height = ""+(this.scrollHeight)+"px";
});
