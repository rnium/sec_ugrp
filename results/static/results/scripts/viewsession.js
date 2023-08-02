const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))


function getSemesterData() {
    let exam_month = $("#monthInput").val().trim();
    let yearInput = $("#yearInput").val().trim();
    let semesterInput = $("#SemesterInput").val().trim();
    exam_month_array = exam_month.split(" ")
    let year_no = parseInt(yearInput)
    let year_semester_no = parseInt(semesterInput)

    if (isNaN(year_no) | isNaN(year_semester_no) | exam_month_array.length != 2) {
        $("#createSemesterAlert").text("Invalid Input");
        $("#createSemesterAlert").show()
        return false;
    }
    if (year_no < 1 | year_no > 4) {
        $("#createSemesterAlert").text("Invalid Year Number");
        $("#createSemesterAlert").show()
        return false;
    }
    if (year_semester_no < 1 | year_semester_no > 2) {
        $("#createSemesterAlert").text("Invalid Semester Number");
        $("#createSemesterAlert").show()
        return false;
    }
    else {
        $("#createSemesterAlert").hide()
    }
    const nth_semester = ((year_no - 1)*2) + year_semester_no;
    data = {
        "year": year_no,
        "year_semester": year_semester_no,
        "semester_no": nth_semester,
        "start_month": exam_month,
        "session": sessionId,
        "added_by": userId,
    }
    return data;
}


function createAPI(api_url, payload, csrftoken, beforeCall, callback_success, callback_error) {
    payload = getSessionData()
    if (payload) {
        $.ajax({
            type: "post",
            url: api_url,
            dataType: "json",
            contentType: "application/json",
            beforeSend: function(xhr){
                xhr.setRequestHeader("X-CSRFToken", csrftoken)
                beforeCall()
            },
            data: JSON.stringify(payload),
            cache: false,
            success: callback_success,
            error: callback_error,
        });
    }
}

$(document).ready(function () {
    $("#create_sem_btn").on('click', ()=>{
        console.log(getSemesterData());
    })
});
