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

$('#container').masonry({
// указываем элемент-контейнер в котором расположены блоки для динамической верстки
	  itemSelector: '.item',
    // columnWidth: 200,
// указываем класс элемента являющегося блоком в нашей сетке
          singleMode: false,
// true - если у вас все блоки одинаковой ширины
	  isResizable: false,
// перестраивает блоки при изменении размеров окна
	  isAnimated: true,
// анимируем перестроение блоков
          animationOptions: {
	      queue: false,
	      duration: 500
	  }
// опции анимации - очередь и продолжительность анимации
});



// $('#btn_find').click( function () {
//     let find_input = $('#find_input').val();
//     console.log(find_input);
// //     const btn_id = this.id.replace('success_application_', '');
// //     const path = '/find/';
//     $.ajax({
//         type: 'POST',
//         mode: 'same-origin',
//         url: pathname,
//         data:{
//             csrfmiddlewaretoken: csrf,
//                 str_find: find_input,
//
//             },
//         success: function () {
//             // window.location.reload();
//             $('html').load(pathname+ ' body');
//         }
//         })
// })