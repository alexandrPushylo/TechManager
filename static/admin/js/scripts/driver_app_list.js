const cw_date = $('.io_current_day');
cw_date.change(function () {
    location.href = '/driver_app_list/'+this.value;
})