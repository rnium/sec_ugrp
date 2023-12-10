function processFormData() {
    let data = {
        reg_num: $('#RegInput').val(),
        session: $('#SessionInp').val(),
        name: $('#NameInp').val(),
        dept: $('#deptInput').val(),
        first_sem_year: $('#firstSemYear').val(),
        first_sem_number: $('#firstSemNumber').val(),
        first_sem_held_in: $('#firstSemHeld').val()
    }
    for (let key in data) {
        if (data[key].length == 0) {
            alert("All the required fields not filled!");
            return;
        }
    }
}

function renderGradesheet(excel_file) {
    let excel_form = new FormData
    excel_form.append("excel", excel_file)
    $.ajax({
        type: "POST",
        url: generate_gradesheet_api,
        data: excel_form,
        contentType: false,
        processData: false,
        beforeSend: function(xhr){
            $("#render-gs-btn").attr("disabled", true)
            $("#process-excel-btn .content").hide(0, ()=>{
                $("#process-excel-btn .spinner").show()
            });
        },
        success: function(response) {
            console.log(response);
        },
        error: function(xhr, status, error) {
            try {
                alert(xhr.responseJSON.details);
            } catch (error_) {
                alert(error);
            }
        },
        complete: function() {
            $("#render-gs-btn").removeAttr("disabled");
            $("#render-gs-btn .spinner").hide(0, ()=>{
                $("#render-gs-btn .content").show()
            });
        }
    });
}

$(document).ready(function () {
    $("#render-gs-btn").on('click', function(){
        excel_file = $("#excelInp")[0].files
        processFormData()
        return;
        if (excel_file.length > 0) {
            renderGradesheet(excel_file[0]);
        } else {
            alert("Please choose an excel file!");
        }
    });
});