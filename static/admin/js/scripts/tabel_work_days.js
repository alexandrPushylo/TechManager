const count_row = $('.day_row').length;
const csrf = $('input[name="csrfmiddlewaretoken"]').val();
const pathname = window.location.pathname;

for (let i=1;i<=count_row;i++) {
    $('#row_'+i).click(function () {
        if ($('#inp_'+i).is(':checked')){
	        $('#inp_'+i).prop('checked', false);
        } else {
	        $('#inp_'+i).prop('checked', true);
        }
        sent(i)
    })
}
function sent(i) {
        let id_day = $('#day_id_'+i).val();
        let status = $('#inp_'+i).is(':checked');
        $.ajax({
        type: 'POST',
        mode: 'same-origin',
        url: pathname,
        data:{
            csrfmiddlewaretoken: csrf,
                id_day: id_day,
                status: status
            }
        })
}
