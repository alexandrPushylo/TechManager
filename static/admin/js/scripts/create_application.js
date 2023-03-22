const count_vehicles = $('.tech_driver_list').length;

for (let i=1;i<=count_vehicles;i++){
    const io_technic = '#io_technic_'+i;
    const io_driver = '#io_driver_'+i;


    $('#select_add_technic_'+i).change(function () {
    $('#select_add_driver_'+i+' > option').prop('hidden',true);
    const th_value = this.value
    let short_name = th_value.replace(' ','').replace('.','');
    $('#select_add_driver_'+i+' > option[short_name="'+short_name+'"]').prop('hidden',false);
    $('#select_add_driver_'+i+' > option:first').prop('selected',true);

    if ($('#select_add_driver_'+i+" option[hidden!='hidden']").length < 2){
        $('#select_add_driver_'+i+" option[hidden!='hidden']:last").prop('selected', true);
        }
        else {
            // $('#select_add_driver_'+i+" option[hidden!='hidden']:first").prop('selected', true);
        }
    })
};
$('#add_vehicle_btn').click(function () {
    const checked_tech = $("#input_tech_add > option:checked").text();
    const inp_tech_cls = $("#input_tech_add").val()
    const checked_driver = $("."+inp_tech_cls+" > option:checked").val();
    let id_tech_driver = $("."+inp_tech_cls+" > option:checked").attr('id_dt');

    if(checked_tech==='---'){return false;}
    if(id_tech_driver===''){id_tech_driver='';}

    const descr_app = $('#description_app_add').val();
    const element_ul = $('.ul_tech_list');
    const current_id = count_vehicles+1;

    const textaria = $('<textarea class="form-control app_description mt-1" name="description_app_list" rows="1">'+descr_app+'</textarea>');
    const div_droup_text_aria = $('<div className="input-group mt-1">');
    const el_btn = $('<button role="button" class="btn btn-danger col-auto btn_del_io"><i class="fa-solid fa-trash"></i></button>');
    const io_dr = $(' <input name="io_driver" type="text" id="io_driver_'+current_id+'" readonly class="form-control" value="'+checked_driver+'">');
    const io_tech = $('<input name="io_technic" type="text" id="io_technic_'+current_id+'" readonly class="form-control" value="'+checked_tech+'">');
    const io_id_td = $('<input name="io_id_tech_driver" type="hidden" value="'+id_tech_driver+'">');
    const div_gr = $('<div class="input-group  tech_driver_list" id="'+current_id+'">');
    const container = $('<div class=" mt-4" id="'+current_id+'">');

    div_droup_text_aria.append(textaria)
    div_gr.append(io_id_td,io_tech, io_dr,el_btn);
    container.append(div_gr,div_droup_text_aria);
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

$("#input_tech_add").change(function (){
    $('.driver_add').prop('hidden',true);
    let v = this.value;
    $('.driver_add.'+v).prop('hidden',false);

    if ($('.driver_add.'+v+" option[hidden!='hidden']").length < 3){
        $('.driver_add.'+v+" option[hidden!='hidden']:last").prop('selected', true);
        }
        else {
            // $('.driver_add.'+v+" option[hidden!='hidden']:first").prop('selected', true);
        }
    return false
});

$('.btn_check_new_tech').click(function () {
    const parentEl = this.parentElement.previousElementSibling.id;

    const curr_io_id_tech_driver = $('#io_id_tech_driver_'+parentEl);
    const curr_io_tech = $('#io_technic_'+parentEl);
    const curr_io_driver = $('#io_driver_'+parentEl);
    const select_add_technic_id = this.parentElement.firstElementChild.id;
    const select_add_driver_id = this.previousElementSibling.id;

    let curr_id_val = $('#'+select_add_driver_id+' option:checked').attr('id_dt');
    const curr_select_tech_val = $('#'+select_add_technic_id).val();
    const curr_select_driver_val = $('#'+select_add_driver_id).val();

    if(curr_id_val===''){curr_id_val='';}

    if (curr_select_tech_val === ''){return false}
    curr_io_id_tech_driver.val(curr_id_val);
    curr_io_tech.val(curr_select_tech_val);
    curr_io_driver.val(curr_select_driver_val);
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

// $('.app_description').on('input', function(){
// 	// this.style.height = '1px';
// 	this.style.height = (this.scrollHeight + 6) + 'px';
// });

