const count_vehicles = $('.tech_driver_list').length;

for (let i=1;i<=count_vehicles;i++){    //OK
    const io_id_tech_driver = '#io_id_tech_driver_'+i;
    const io_tech_name_id = '#io_tech_name_id_'+i;

    let v1 = $(io_id_tech_driver).val()
    let v2 = $(io_tech_name_id).val()

    $('#select_add_technic_'+i+' option[value='+v2+']').prop('selected', true);
    $('.select_add_driver_'+i+'.select_td_'+v2).prop('hidden', false);
    $('.select_add_driver_'+i+'.select_td_'+v2+' option[value='+v1+']').prop('selected', true);

    $('#select_add_technic_'+i).change(function () {
    $('.select_add_driver_'+i).prop('hidden',true);

    let tech_name_id = this.value;
    $('.select_add_driver_'+i+'.select_td_'+tech_name_id).prop('hidden', false);

    if ($('.select_add_driver_'+i+'.select_td_'+tech_name_id+" option[hidden!='hidden']").length === 2){
        $('.select_add_driver_'+i+'.select_td_'+tech_name_id+" option[hidden!='hidden']:last").prop('selected', true);
        }
    })
}

$('#add_vehicle_btn').click(function () {
    const tech_NAME = $("#input_tech_add > option:checked").text();
    const tech_ID = $("#input_tech_add > option:checked").val();

    let driver_ID = $(".select_td_add_"+tech_ID+" > option:checked").val();
    const driver_NAME = $(".select_td_add_"+tech_ID+" > option:checked").text();

    if(tech_NAME==='---'){return false;}

    const descr_app = $('#description_app_add').val();
    const element_ul = $('.ul_tech_list');
    const current_id = count_vehicles+1;

    const textaria = $('<textarea class="form-control app_description mt-1" name="description_app_list" rows="1">'+descr_app+'</textarea>');
    const div_droup_text_aria = $('<div className="input-group mt-1">');
    const el_btn = $('<button role="button" class="btn btn-danger col-auto btn_del_io"><i class="fa-solid fa-trash"></i></button>');

    const io_dr = $(' <input type="text" id="io_driver_'+current_id+'" readonly class="form-control" value="'+driver_NAME+'">');
    const io_tech = $('<input type="text" id="io_technic_'+current_id+'" readonly class="form-control" value="'+tech_NAME+'">');

    const io_id_td = $('<input name="io_id_tech_driver" type="hidden" value="'+driver_ID+'">');
    const io_id_tech = $('<input name="io_id_tech_name" type="hidden" value="'+tech_ID+'">');

    const div_gr = $('<div class="input-group  tech_driver_list" id="'+current_id+'">');
    const container = $('<div class=" mt-4" id="'+current_id+'">');

    div_droup_text_aria.append(textaria)
    div_gr.append(io_id_tech, io_id_td, io_tech, io_dr,el_btn);
    container.append(div_gr, div_droup_text_aria);
    element_ul.append(container);

    $('.btn_del_io').click(function (e) {
    this.parentElement.parentElement.remove();
    return false;
    });

    $('.driver').prop('hidden',true);
    $('#description_app_add').val('');
    $("#input_tech_add > option:first").prop('selected', true);
    $('.driver_add').prop('hidden',true);

    $('.app_description').each(function () {
    this.style.height = ""+(this.scrollHeight)+"px";
    });
    return false;
});

$("#input_tech_add").change(function (){    //OK
    $('.driver_add').prop('hidden',true);
    let tech_name_id = this.value;
    $('.select_td_add_'+tech_name_id).prop('hidden',false);

    if ($('.select_td_add_'+tech_name_id+" option[hidden!='hidden']").length < 3){
        $('.select_td_add_'+tech_name_id+" option[hidden!='hidden']:last").prop('selected', true);
        }
    return false
});

$('.btn_check_new_tech').click(function () {    //OK
    const parentEl = this.parentElement.previousElementSibling.id;

    const curr_io_id_tech_driver = $('#io_id_tech_driver_'+parentEl);
    const io_tech_name_id = $('#io_tech_name_id_'+parentEl);

    const curr_io_tech = $('#io_technic_'+parentEl);
    const curr_io_driver = $('#io_driver_'+parentEl);

    const tech_name_NAME = $('#select_add_technic_'+parentEl+' option:checked').text();
    const tech_name_ID = $('#select_add_technic_'+parentEl+' option:checked').val();

    const driver_NAME = $('.select_td_'+tech_name_ID+'.select_add_driver_'+parentEl+' option:checked').text();
    const driver_ID = $('.select_td_'+tech_name_ID+'.select_add_driver_'+parentEl+' option:checked').val();

    if (tech_name_ID != ''){
        curr_io_id_tech_driver.val(driver_ID);
        io_tech_name_id.val(tech_name_ID);

        curr_io_tech.val(tech_name_NAME);
        curr_io_driver.val(driver_NAME);
        }

    const parEl = this.parentElement.id;
    $('#'+parEl).prop('hidden',true);
    return false;
});

$('.btn_check_cancel_tech').click(function () {
    const parEl = this.parentElement.id;
    $('#'+parEl).prop('hidden',true);
    return false
})

$('.btn_edit_io').click(function (e) {
    const parent_id = this.parentElement.id;
    const div_edit_io = $('#div_edit_io_'+parent_id);
    div_edit_io.prop('hidden',false);
    return false;
});

$('.btn_del_io').click(function (e) {
    this.parentElement.parentElement.remove();
    return false;
});

$('.app_description').each(function () {
    this.style.height = ""+(this.scrollHeight)+"px";
});
