const id_tech = $('#io_id_tech');
const io_tech_name = $('#io_name_tech');
const io_tech_type = $('#io_type_tech');
const io_att_drv = $('#io_att_drv');

$('#name_tech_select> option[value="'+io_tech_name.val()+'"]').prop('selected', true);
$('#type_tech_select> option[value="'+io_tech_type.val()+'"]').prop('selected', true);
$('#att_drv_tech_select> option[value="'+io_att_drv.val()+'"]').prop('selected', true);

$('.app_description').each(function () {
    this.style.height = ""+(this.scrollHeight)+"px";
});
