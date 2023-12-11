function processFormData() {
    let data = {
        reg_num: $('#RegInput').val(),
        session: $('#SessionInp').val(),
        name: $('#NameInp').val(),
        dept: $('#deptInput').val(),
        first_sem_year: $('#firstSemYear').val(),
        first_sem_number: $('#firstSemNumber').val(),
        first_sem_held_in: $('#firstSemHeld').val(),
        final_res_credit: $('#finalResCredit').val(),
        final_res_cgpa: $('#finalResCG').val(),
        final_res_letter_grade: $('#finalResLG').val(),
    }
    for (let key in data) {
        if (data[key].length == 0) {
            alert("All the required fields not filled properly!");
            return false;
        }
    }
    let second_sem_year = $("#secondSemYear").val();
    let second_sem_number = $("#secondSemNumber").val();
    let second_sem_held_in = $("#secondSemHeld").val();
    if (second_sem_year.length == 0 
        | second_sem_number.length == 0 
        | second_sem_held_in.length == 0  ) {
            data.num_semesters = 1
    } else {
        data.num_semesters = 2;
        data.second_sem_year = second_sem_year;
        data.second_sem_number = second_sem_number;
        data.second_sem_held_in = second_sem_held_in;
    }
    return data;
}

function renderGradesheet(data, excel_file) {
    let excel_form = new FormData
    excel_form.append("data", JSON.stringify(data))
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
            var link = response.url;
            if (link) {
                var newTab = window.open(link, '_blank');
                newTab.focus();
            } else {
                console.error('No link found in the API response.');
            }
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
        let data = processFormData()
        if (data == false) { 
            return;
        }
        if (excel_file.length > 0) {
            renderGradesheet(data, excel_file[0]);
        } else {
            alert("Please choose an excel file!");
        }
    });
});