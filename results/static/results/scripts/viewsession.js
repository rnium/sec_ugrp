const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))


function hideModal(modalId) {
    $(`#${modalId}`).modal('hide');
    
}


function showError(errorContainer, msg) {
    $(`#${errorContainer}`).text(msg)
    $(`#${errorContainer}`).show(1200,()=>{
        setTimeout(()=>{
            $(`#${errorContainer}`).hide()
        }, 3000)
    })
}


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

function renderAndInsertNewSemester(response, containerId) {
    let session = `<div class="col-md-6 p-0">
                        <a href="${response['view_url']}" class="running-semester">
                            <div class="sem-codename">
                                <span class="year">${response['year']}</span>
                                <span>-</span>
                                <span class="semester">${response['year_semester']}</span>
                            </div>
                            <div class="info">
                                <div class="semester-no">${response['semester_name']}</div>
                                <div class="exam-start-month">
                                    <i class='bx bxs-calendar me-2 fs-5'></i>
                                    <div class="month fs-6">${response['start_month']}</div>
                                </div>
                            </div>    
                        </a>
                    </div>`
    $(`#${containerId}`).append(session);
    console.log(session);
}

function createSemester() {
    payload = getSemesterData()
    if (payload) {
        $.ajax({
            type: "post",
            url: create_semester_api,
            dataType: "json",
            contentType: "application/json",
            beforeSend: function(xhr){
                $("#createSemesterAlert").hide()
                $("#create_sem_btn").attr("disabled", true)
                xhr.setRequestHeader("X-CSRFToken", csrftoken)
            },
            data: JSON.stringify(payload),
            cache: false,
            success: function(response) {
                $("#create_sem_btn").removeAttr("disabled");
                hideModal("newSemesterEntryModal");
                renderAndInsertNewSemester(response, "semesterContainer")
            },
            error: function(xhr, status, error) {
                $("#create_sem_btn").removeAttr("disabled");
                showError("createSemesterAlert", xhr.responseJSON['detail'])
            },
        });
    }
}



$(document).ready(function () {
    $("#create_sem_btn").on('click', createSemester)
});
