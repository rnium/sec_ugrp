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
        if (excel_file.length > 0) {
            renderGradesheet(excel_file[0]);
        } else {
            alert("Please choose an excel file!");
        }
    });
});