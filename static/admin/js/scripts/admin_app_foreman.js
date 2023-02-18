const cw_date = $('.io_current_day');
cw_date.change(function () {
    location.href = '/applications/'+this.id+'/'+this.value;
})