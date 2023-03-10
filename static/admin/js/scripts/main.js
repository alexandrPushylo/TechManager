$('.app_description').each(function () {
    this.style.height = ""+(this.scrollHeight+5)+"px";
});

const cw_date = $('.io_current_day');
cw_date.change(function () {
    location.href = '/applications/'+this.value;
})

$('.div_td').click(function () {
    location.href = '/append_in_hos_tech/'+this.id;

})

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

$('.driver_name_link').click(function () {
    if(this.id){
        location.href = '/personal_application/'+$('.io_current_day').val()+'/'+this.id;
    }

})

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