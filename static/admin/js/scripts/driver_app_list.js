const cw_date = $('.io_current_day');
cw_date.change(function () {
    location.href = '/driver_app_list/'+this.value;
})

$('.app_description').each(function () {
    this.style.height = ""+(this.scrollHeight)+"px";
});