const count_vehicles = $('.input_tech').length;
for(let i=1;i<=count_vehicles;i++){
    const btn_reset = '#btn_reset_'+i;
    const io_vehicle = '#io_vehicle_'+i;
    const io_driver = '#io_driver_'+i;
    const select_tech_name = '#select_tech_name_'+i;
    const select_tech_drv = '.select_tech_drv_'+i;

    const io_vehicle_id_val = $(io_vehicle).val();
    const io_driver_id_val = $(io_driver).val();

    $('#select_tech_name_'+i+'> option[value="'+ io_vehicle_id_val +'"]').prop('selected',true);
    $('#select_tech_drv_'+io_vehicle_id_val+select_tech_drv).prop('disabled', false).prop('hidden',false);
    $('#select_tech_drv_'+io_vehicle_id_val+select_tech_drv+' >option[value="'+ io_driver_id_val +'"]').prop('selected',true);

    $(btn_reset).click(function () {
        $(select_tech_drv).prop('disabled', true).prop('hidden',true);
        $('#select_tech_drv_'+io_vehicle_id_val+select_tech_drv).prop('disabled', false).prop('hidden',false);
        $('#select_tech_name_'+i+'> option[value="'+ io_vehicle_id_val +'"]').prop('selected',true);
        $('#select_tech_drv_'+io_vehicle_id_val+select_tech_drv+' >option[value="'+ io_driver_id_val +'"]').prop('selected',true);
        return false;
    });

    $(select_tech_name).change(function () {
        $(select_tech_drv).prop('disabled', true).prop('hidden',true);
        $('#select_tech_drv_'+this.value+select_tech_drv).prop('disabled', false).prop('hidden',false);
    });
}

$('.app_description').each(function () {
    this.style.height = ""+(this.scrollHeight)+"px";
});

$('#container').masonry({
// указываем элемент-контейнер в котором расположены блоки для динамической верстки
	  itemSelector: '.item',
    // columnWidth: 200,
// указываем класс элемента являющегося блоком в нашей сетке
          singleMode: true,
// true - если у вас все блоки одинаковой ширины
	  isResizable: true,
// перестраивает блоки при изменении размеров окна
	  isAnimated: true,
// анимируем перестроение блоков
          animationOptions: {
	      queue: false,
	      duration: 500
	  }
// опции анимации - очередь и продолжительность анимации
});