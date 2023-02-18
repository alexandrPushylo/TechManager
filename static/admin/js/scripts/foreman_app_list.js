const cw_date = $('.io_current_day');
cw_date.change(function () {
    location.href = '/foreman_app_list/'+this.value;
})