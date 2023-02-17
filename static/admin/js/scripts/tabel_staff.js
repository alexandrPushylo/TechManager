const count_row = $('.user_row').length;

for (let i=1;i<=count_row;i++) {

    $('#row_'+i).click(function () {
        if ($('#inp_'+i).is(':checked')){
	        $('#inp_'+i).prop('checked', false);
        } else {
	        $('#inp_'+i).prop('checked', true);
        }
    })
}

const notice = $('#notice_stat');
notice.hide()
if (notice.attr('status')){
    notice.show()
    setTimeout(function() { notice.hide(); }, 2000)
}