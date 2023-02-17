const cw_date = $('.io_current_day');
cw_date.change(function () {
    location.href = '/personal_application/'+this.value+'/'+this.id;
})