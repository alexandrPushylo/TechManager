window.print();
$('.app_description').each(function () {
    this.style.height = ""+(this.scrollHeight)+"px";
});

$('.app_description').on('input', function(){
	this.style.height = '1px';
	this.style.height = (this.scrollHeight + 6) + 'px';
});


