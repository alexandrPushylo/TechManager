//auto resize <textarea>
$('.app_description').each(function () {
    this.style.height = ""+(this.scrollHeight)+"px";
});
$('.app_description').on('input', function(){
	this.style.height = '1px';
	this.style.height = (this.scrollHeight + 6) + 'px';
});

const cw_date = $('.io_current_day');
cw_date.change(function () {
    location.href = '/today_app/'+this.value;
})