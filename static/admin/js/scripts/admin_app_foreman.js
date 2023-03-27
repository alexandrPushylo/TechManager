const cw_date = $('.io_current_day');
cw_date.change(function () {
    location.href = '/applications/'+this.id+'/'+this.value;
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