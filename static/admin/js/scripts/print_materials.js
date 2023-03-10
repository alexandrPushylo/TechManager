window.print();
$('.app_description').each(function () {
    this.style.height = ""+(this.scrollHeight+10)+"px";
});

$('.app_description').on('input', function(){
	this.style.height = '1px';
	this.style.height = (this.scrollHeight + 10) + 'px';
});


