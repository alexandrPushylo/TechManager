const cw_date = $('.io_current_day');
cw_date.change(function () {
    location.href = '/tech_list/'+this.value;
})