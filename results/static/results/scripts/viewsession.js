const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))


function hideModal(modalId) {
    $(`#${modalId}`).modal('hide');
    
}


function showError(errorContainer, msg) {
    $(`#${errorContainer}`).text(msg)
    $(`#${errorContainer}`).show(200,()=>{
        setTimeout(()=>{
            $(`#${errorContainer}`).hide()
        }, 60000)
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
                        <a href="${response['view_url']}" class="semester-item shadow-sm m-1 running-semester">
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
    $("#no-content-semesters").remove();
    $(`#${containerId}`).append(session);
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

function setupAvatar(image_file, registration) {
    let image_form = new FormData
    image_form.append("dp", image_file)
    image_form.append("registration", registration)
    $.ajax({
        type: "post",
        url: set_student_avatar_api,
        data: image_form,
        contentType: false,
        processData: false,
        error: function(xhr, error, status) {
            showError("createStudentAlert", JSON.stringify(xhr.responseJSON))
        },
        complete: function() {
            location.reload()
        }
    });
}

function checkStudentForm() {
    let input_fields = $(".studentinput-must")
    for (let field of input_fields) {
        field_val = $(field).val()
        if (field_val.length < 1) {
            $(field).focus()
            showError("Please fill the field")
            return false
        }
    }
    return true
}


function createStudentAccount(){
    let form_is_valid = checkStudentForm()
    if (!form_is_valid) {
        return false
    }
    let data = {
        registration: $("#registrationNoInput").val().trim(),
        first_name: $("#firstNameInput").val().trim(),
        last_name: $("#lastNameInput").val().trim(),
        session: sessionId
    }
    
    let payload = JSON.stringify(data)
    $.ajax({
        type: "post",
        url: create_student_account_api,
        dataType: "json",
        contentType: "application/json",
        beforeSend: function(xhr){
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
            $("#create-student-btn").attr('disabled', true);
        },
        data: payload,
        cache: false,
        success: function(response) {
            avatar_files = $("#dp")[0].files
            if (avatar_files.length > 0) {
                setupAvatar(avatar_files[0], response.registration)
            } else {
                location.reload()
            }
        },
        error: function(xhr, status, error) {
            $("#create-student-btn").removeAttr("disabled");
            showError("createStudentAlert", JSON.stringify(xhr.responseJSON));
        },
    });
}

// Delete session
function delete_session() {
    let showAlert = (msg)=>{
        $("#deleteSessionModal .alert").text(msg)
        $("#deleteSessionModal .alert").show()
    }
    let password = $(`#deleteSessionModal input[type="password"]`).val().trim()
    if (password.length == 0) {
        showAlert("Please enter your password");
        return
    }
    payload = {
        password: password
    }
    if (payload) {
        $.ajax({
            type: "post",
            url: delete_session_api,
            dataType: "json",
            contentType: "application/json",
            beforeSend: function(xhr){
                $("#confirm-del-btn").attr("disabled", true)
                $("#deleteSemesterModal .alert").hide()
                xhr.setRequestHeader("X-CSRFToken", csrftoken)
            },
            data: JSON.stringify(payload),
            cache: false,
            success: function(response) {
                $('#deleteSessionModal .alert').removeClass('alert-warning');
                $('#deleteSessionModal .alert').addClass('alert-info');
                showAlert("Complete")
                setTimeout(()=>{
                    window.location.href = response.dept_url
                }, 1000)
            },
            error: function(xhr, status, error) {
                showAlert(xhr.responseJSON.details)
                $("#confirm-del-btn").removeAttr('disabled');
            }
        });
    }
}

// Excel upload
function uploadExcel(excel_file) {
    let excel_form = new FormData
    excel_form.append("excel", excel_file)
    $.ajax({
        type: "post",
        url: create_student_via_excel_api,
        data: excel_form,
        contentType: false,
        processData: false,
        beforeSend: function(xhr){
            $("#process-excel-btn").attr("disabled", true)
            $("#process-excel-btn .content").hide(0, ()=>{
                $("#process-excel-btn .spinner").show()
            });
        },
        success: function(response) {
            $("#summary_list").html(response.summary);
            $("#summary_list_container").show(200)
        },
        error: function(xhr, status, error) {
            try {
                alert(xhr.responseJSON.details);
            } catch (error_) {
                alert(error);
            }
        },
        complete: function() {
            $("#process-excel-btn").removeAttr("disabled");
            $("#process-excel-btn .spinner").hide(0, ()=>{
                $("#process-excel-btn .content").show()
            });
        }
    });
}



$(document).ready(function () {
    $("#create_sem_btn").on('click', createSemester);
    $("#create-student-btn").on('click', createStudentAccount);
    $("#confirm-del-btn").on('click', delete_session);
    $("#process-excel-btn").on('click', function() {
        excel_file = $("#excelFile")[0].files
        if (excel_file.length > 0) {
            uploadExcel(excel_file[0]);
        } else {
            alert("Please choose an excel file!");
        }
    })
});
