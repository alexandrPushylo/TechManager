$('.app_description').each(function () {
    this.style.height = ""+(this.scrollHeight+5)+"px";
});

const cw_date = $('.io_current_day');
cw_date.change(function () {
    location.href = '/applications/'+this.value;
})

// $('.div_td').click(function () {
//     location.href = '/append_in_spec_tech/'+this.id;
//
// })

const csrf = $('input[name="csrfmiddlewaretoken"]').val();
const pathname = window.location.pathname;

$('.btn_driver_panel').click(function () {
    if($('.driver_panel').is(':hidden')){
            $('.driver_panel').prop('hidden',false)
        }else {
            $('.driver_panel').prop('hidden',true)
        }
    $.ajax({
        type: 'POST',
        mode: 'same-origin',
        url: pathname,
        data: {
            csrfmiddlewaretoken: csrf,
                panel: $('.driver_panel').is(':hidden')
        }
    })
    return false
})

$('#btn_app_copy').click(function () {
    const select_app = $('#select_copy_app');
    const date_copy_app = $('#date_copy_app');

    if (date_copy_app.val() != ''){
        location.href = '/copy_app/'+select_app.val()+'/'+date_copy_app.val();
    }
    return false;
});

$('.driver_name_link').click(function () {
    if(this.id){
        location.href = '/personal_application/'+$('.io_current_day').val()+'/'+this.id;
    }
})

// $('.technic_name_link').click(function () {
//     if(this.id){
//         location.href = '/get_id_tech_name/'+$('.io_current_day').val()+'/'+this.id;
//     }
// })

$('#btn_show_tech').click(function () {
    sent('technics')
    return false
})

$('#btn_show_all').click(function () {
    sent('all')
    return false
})

$('#btn_show_mater').click(function () {
    sent('materials')
})

function sent(i) {
        $.ajax({
        type: 'POST',
        mode: 'same-origin',
        url: pathname,
        data:{
            csrfmiddlewaretoken: csrf,
                filter: i
            },
        success: function() {
            window.location.reload();
            }
        })
}


$('#btn_sub_change_drv').click(function () {
    const s_from = $('#select_from_drv').val();
    const s_to = $('#select_to_drv').val();
    // console.log(s_from,'>>',s_to);
    $.ajax({
        type: 'POST',
        mode: 'same-origin',
        url: pathname,
        data:{
            csrfmiddlewaretoken: csrf,
                td_from: s_from,
                td_to:s_to
            },
        success: function() {
            window.location.reload();
            }
        })
})

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

// $('.btn_T').click(function () {
//     const btn_id = this.id.replace('success_application_', '');
//     const path = '/success_app/'+btn_id;
//     $.ajax({
//         type: 'POST',
//         mode: 'same-origin',
//         url: path,
//         data:{
//             csrfmiddlewaretoken: csrf,
//                 app_id: btn_id,
//
//             },
//         success: function () {
//             $('#per_'+btn_id).load(path+' #'+btn_id);
//         }
//         })
// })
