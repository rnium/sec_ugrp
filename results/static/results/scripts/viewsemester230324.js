const DropCourses = {
    addition:[],
    removal:[],
    get_data: function() {
        return {"add_courses": this.addition, "remove_courses":this.removal}
    },
    is_empty: function() {
        return ((this.addition.length + this.removal.length) == 0);
    },
    indexAtAddlist: function(value) {
        return this.addition.findIndex(i => i == value);
    },
    indexAtRemlist: function(value) {
        return this.removal.findIndex(i => i == value);
    },
    add2addition: function(value) {
        this.addition.push(value)
    },
    add2removal: function(value) {
        this.removal.push(value);
    },
    deleteXaddition: function(value) {
        let idx = this.indexAtAddlist(value)
        this.addition.splice(idx, 1);
    },
    deleteXremoval: function(value) {
        let idx = this.indexAtRemlist(value);
        this.removal.splice(idx, 1);
    }
}


function showNotification(msg) {
    const elem = document.getElementById('notificationModal')
    const toastBody = document.getElementById('modal-body');
    toastBody.innerText = msg;
    const mBootstrap = new bootstrap.Modal(elem);
    mBootstrap.show()
}

// const saveBtn = document.getElementById("save-btn")
// saveBtn.addEventListener('click', ()=>{
//     // do some saving stuff
//     showNotification("Saved Successfully!")
// })


function showDevModal(id) {
    const elem = document.getElementById(id)
    const mBootstrap = new bootstrap.Modal(elem);
    mBootstrap.show()
}


function showError(alertContainer, msg) {
    $(`#${alertContainer}`).removeClass("alert-warning");
    $(`#${alertContainer}`).addClass("alert-danger");
    $(`#${alertContainer}`).text(msg)
    $(`#${alertContainer}`).show(200,()=>{
        setTimeout(()=>{
            $(`#${errorContainer}`).hide()
        }, 60000)
    })
}

function showInfo(alertContainer, msg) {
    $(`#${alertContainer}`).removeClass("alert-danger");
    $(`#${alertContainer}`).addClass("alert-warning");
    $(`#${alertContainer}`).text(msg)
    $(`#${alertContainer}`).show(200,()=>{
        setTimeout(()=>{
            $(`#${errorContainer}`).hide()
        }, 60000)
    })
}


function hideModal(modalId) {
    $(`#${modalId}`).modal('hide'); 
}



const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))


function getNewCourseData() {
    let courseCodeIn = $("#courseCodeInput").val().trim();
    let courseTitleIn = $("#courseTitleInput").val().trim();
    let totalMarksIn = parseFloat($("#totalMarksInput").val().trim());
    let creditsIn = parseFloat($("#courseCreditsInput").val().trim());
    let partAMarksIn = parseFloat($("#partAmarksInput").val().trim());
    let partAMarksInFinal = parseFloat($("#partAmarksInputFinal").val().trim());
    let partBMarksIn = parseFloat($("#partBmarksInput").val().trim());
    let partBMarksInFinal = parseFloat($("#partBmarksInputFinal").val().trim());
    let incourseMarksIn = parseFloat($("#inCourseMarksInput").val().trim());
    let selectedCourseType = $('input[name="courseTypeOptions"]:checked').val();
    let is_theory_course = (selectedCourseType == 'theory')
    let courseCodeArray = courseCodeIn.split(" ")
    let courseCodeNumber = parseInt(courseCodeArray[1])
    
    if (is_theory_course) {
        if (isNaN(totalMarksIn)
            || isNaN(creditsIn) 
            || isNaN(partAMarksIn)
            || isNaN(partBMarksIn) 
            || isNaN(incourseMarksIn) 
            || isNaN(partAMarksInFinal)
            || isNaN(partBMarksInFinal)) {
            $("#createCourseAlert").text("Invalid Input(s), please fill correctly");
            $("#createCourseAlert").show()
            return false;
        }
    } else {
        if (isNaN(totalMarksIn) || isNaN(creditsIn)) {
            $("#createCourseAlert").text("Invalid Input(s), please fill correctly");
            $("#createCourseAlert").show()
            return false;
        }
        partAMarksIn = 0;
        partAMarksInFinal = 0;
        partBMarksIn = 0;
        partBMarksInFinal = 0;
        incourseMarksIn = 0;
    }

    if (courseCodeIn.length == 0 | courseTitleIn.length == 0 | selectedCourseType.length == 0) {
        $("#createCourseAlert").text("Please fill all the fields");
        $("#createCourseAlert").show()
        return false;
    }
    if (courseCodeArray.length != 2 | isNaN(courseCodeNumber)) {
        $("#createCourseAlert").text("Invalid Course code! Please enter correctly.");
        $("#createCourseAlert").show()
        return false;
    }
    if (((partAMarksInFinal+partBMarksInFinal+incourseMarksIn) > totalMarksIn) && is_theory_course) {
        $("#createCourseAlert").text("Invalid Marks Distribution!");
        $("#createCourseAlert").show();
        return false;
    }
    else {
        $("#createCourseAlert").hide()
    }
    
    data = {
        "semester": semesterId,
        "code": courseCodeIn,
        "title": courseTitleIn,
        "course_credit": creditsIn,
        "total_marks": totalMarksIn,
        "part_A_marks": partAMarksIn,
        "part_A_marks_final": partAMarksInFinal,
        "part_B_marks": partBMarksIn,
        "part_B_marks_final": partBMarksInFinal,
        "incourse_marks": incourseMarksIn,
        "is_theory_course": is_theory_course,
        "is_carry_course": $("#switch-addascarrycourse").is(':checked')
    }

    return data;
}

function getRenderTabulationData() {
    let data = {
        render_config: {
            tabulation_title: "",
            tabulation_exam_time: "",
            rows_per_page: 10,
            font_offset: 0,
            margin_x: 1, // 1cm
            margin_y: 1,
        },
        footer_data_raw: {
            chairman: "",
            controller: "",
            committee: [],
            tabulators: [],
        }
    }
    // render config
    data.render_config.tabulation_title = $("#tabulation-title").val().trim()
    data.render_config.tabulation_exam_time = $("#tabulation-exam-time").val().trim()
    // footer data
    let chairman_name = $("#chairman").val().trim()
    let controller_name = $("#controller").val().trim()
    if (chairman_name.length > 0) {
        data.footer_data_raw.chairman = chairman_name
    }
    if (controller_name.length > 0) {
        data.footer_data_raw.controller = controller_name
    }
    // exam committee members
    let committee_arr = $("input.member")
    $.each(committee_arr, function (indexInArray, valueOfElement) { 
        let val = $(valueOfElement).val().trim()
        if (val.length > 0) {
            data.footer_data_raw.committee.push(val)
        }

    });
    // tabulators
    let tabulators_arr = $("input.tabulator")
    $.each(tabulators_arr, function (indexInArray, valueOfElement) { 
        let val = $(valueOfElement).val().trim()
        if (val.length > 0) {
            data.footer_data_raw.tabulators.push(val)
        }

    });
    return data;
}

function createCourse() {
    payload = getNewCourseData()
    if (payload) {
        $.ajax({
            type: "post",
            url: create_course_api,
            dataType: "json",
            contentType: "application/json",
            beforeSend: function(xhr){
                $("#createCourseAlert").hide()
                $("#createCourseAddBtn").attr("disabled", true)
                xhr.setRequestHeader("X-CSRFToken", csrftoken)
            },
            data: JSON.stringify(payload),
            cache: false,
            success: function(response) {
                hideModal("newSemesterEntryModal");
                showInfo("createCourseAlert", "New course created successfully! Reloading page in a moment")
                setTimeout(()=>{location.reload()}, 1000)
            },
            error: function(xhr, status, error) {
                $("#createCourseAddBtn").removeAttr("disabled");
                showError("createCourseAlert", error);
            },
        });
    }
}

function updateDropcourse() {
    if (DropCourses.is_empty()) {
        return
    }
    $.ajax({
        type: "post",
        url: drop_course_update_api,
        dataType: "json",
        contentType: "application/json",
        beforeSend: function(xhr){
            $("#dropCourseModalAlert").hide()
            $("#selectionConfirmBtn").attr("disabled", true)
            xhr.setRequestHeader("X-CSRFToken", csrftoken)
        },
        data: JSON.stringify(DropCourses.get_data()),
        cache: false,
        success: function(response) {
            showInfo("dropCourseModalAlert", "Drop courses updated successfully! Reloading page in a moments")
            setTimeout(()=>{location.reload()}, 3000)
        },
        error: function(xhr, status, error) {
            $("#selectionConfirmBtn").removeAttr("disabled");
            showError("dropCourseModalAlert", error);
        },
    });
}

function setTabulationCardProps(response) {
    $("#tabulation-thumb").attr('src', response['thumbnail']);
    $("#tabulation-filename").text(response['tabulation_name']);
    $("#tabulation-download").attr('href', response['download_url']);
    let render_time = new Date(response['render_time'])
    let render_info = `Last render: ${render_time.toLocaleString()} by ${response['renderer_user']}`
    $('#render_info').text(render_info);
    let targetElement = document.getElementById("tabulation-main");
    targetElement.scrollIntoView({ behavior: 'smooth' });
    $("#tabulation-card").show(200)
}

function renderTabulation() {
    let payload = getRenderTabulationData()
    if (payload) {
        $.ajax({
            type: "post",
            url: render_tabulation_api,
            dataType: "json",
            contentType: "application/json",
            beforeSend: function(xhr){
                $("#render-tabulation-btn").attr("disabled", true)
                $("#render-tabulation-btn .content").hide(0, ()=>{
                    $("#render-tabulation-btn .spinner").show()
                });
                xhr.setRequestHeader("X-CSRFToken", csrftoken)
            },
            data: JSON.stringify(payload),
            cache: false,
            success: function(response) {
                setTabulationCardProps(response)
            },
            error: function(xhr, status, error) {
                alert(error)
            },
            complete: function() {
                $("#render-tabulation-btn").removeAttr("disabled");
                $("#render-tabulation-btn .spinner").hide(0, ()=>{
                    $("#render-tabulation-btn .content").show()
                });
            }
        });
    }
}


function change_running_status() {
    let showAlert = (msg)=>{
        $("#changeWithPasswordModal .alert").text(msg)
        $("#changeWithPasswordModal .alert").show()
    }
    let password = $(`#changeWithPasswordModal input[type="password"]`).val().trim()
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
            url: change_running_status_api,
            dataType: "json",
            contentType: "application/json",
            beforeSend: function(xhr){
                $("#confirm-change-btn").attr("disabled", true)
                $("#changeWithPasswordModal .alert").hide()
                xhr.setRequestHeader("X-CSRFToken", csrftoken)
            },
            data: JSON.stringify(payload),
            cache: false,
            success: function(response) {
                $('#changeWithPasswordModal .alert').removeClass('alert-warning');
                $('#changeWithPasswordModal .alert').addClass('alert-info');
                showAlert("Complete")
                setTimeout(()=>{
                    location.reload()
                }, 1000)
            },
            error: function(xhr, status, error) {
                showAlert(xhr.responseJSON.details)
                $("#confirm-change-btn").removeAttr('disabled');
            }
        });
    }
}

function delete_semester() {
    let showAlert = (msg)=>{
        $("#deleteSemesterModal .alert").text(msg)
        $("#deleteSemesterModal .alert").show()
    }
    let password = $(`#deleteSemesterModal input[type="password"]`).val().trim()
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
            url: delete_semester_api,
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
                $('#deleteSemesterModal .alert').removeClass('alert-warning');
                $('#deleteSemesterModal .alert').addClass('alert-info');
                showAlert("Complete")
                setTimeout(()=>{
                    window.location.href = response.session_url
                }, 1000)
            },
            error: function(xhr, status, error) {
                showAlert(xhr.responseJSON.details)
                $("#confirm-del-btn").removeAttr('disabled');
            }
        });
    }
}

// update semester
function getSemesterData() {
    let exam_month = $("#monthInput").val().trim();
    let exam_duration = $("#durationInput").val().trim();
    let yearInput = $("#yearInput").val().trim();
    let semesterInput = $("#SemesterInput").val().trim();
    let repeatCountInput = $("#repeatCount").val().trim();
    let partNoInput = $("#semesterPartNo").val().trim();
    exam_month_array = exam_month.split(" ")
    let year_no = parseInt(yearInput)
    let year_semester_no = parseInt(semesterInput)
    let repeat_count = parseInt(repeatCountInput)
    let part_no = parseInt(partNoInput)

    if (isNaN(part_no)) {
        part_no = 0;
    }

    if (isNaN(year_no) | isNaN(year_semester_no) | exam_month_array.length != 2) {
        $("#updateSemesterAlert").text("Invalid Input");
        $("#updateSemesterAlert").show()
        return false;
    }
    if (year_no < 1 | year_no > 4) {
        $("#updateSemesterAlert").text("Invalid Year Number");
        $("#updateSemesterAlert").show()
        return false;
    }
    if (year_semester_no < 1 | year_semester_no > 2) {
        $("#updateSemesterAlert").text("Invalid Semester Number");
        $("#updateSemesterAlert").show()
        return false;
    }
    else {
        $("#updateSemesterAlert").hide()
    }
    const nth_semester = ((year_no - 1)*2) + year_semester_no;
    data = {
        "year": year_no,
        "year_semester": year_semester_no,
        "semester_no": nth_semester,
        "start_month": exam_month,
        "part_no": part_no,
    }
    if (exam_duration.length > 0) {
        data.exam_duration = exam_duration;
    }
    if (nth_semester == 8 && !isNaN(repeat_count)) {
        data['repeat_number'] = repeat_count
    }
    return data;
}

function updateSemester() {
    payload = getSemesterData()
    if (payload) {
        $.ajax({
            type: "PATCH",
            url: semester_update_api,
            dataType: "json",
            contentType: "application/json",
            beforeSend: function(xhr){
                $("#update-semester-btn").attr("disabled", true)
                xhr.setRequestHeader("X-CSRFToken", csrftoken)
            },
            data: JSON.stringify(payload),
            cache: false,
            success: function(response) {
                showInfo('updateSemesterAlert', "Updated successfully");
                setTimeout(()=>{
                    window.location.href = session_url;
                }, 1000)
            },
            error: function(xhr, status, _error) {
                try {
                    showError("updateSemesterAlert", JSON.stringify(xhr.responseJSON));
                } catch (error) {
                    showError("updateSemesterAlert", _error);
                }
            },
            complete: function() {
                $("#update-semester-btn").removeAttr("disabled");
            }
        });
    }
}

function delete_semesterenroll() {
    if (!confirm("Are you sure to delete this entry?")) {
        return
    }
    let enrollment_id = $(this).data('enrollid');
    let payload = {enrollment_id: enrollment_id}
    $.ajax({
        type: "post",
        url: delete_enrollment_api,
        dataType: "json",
        contentType: "application/json",
        beforeSend: function(xhr){
            $(this).attr("disabled", true);
            xhr.setRequestHeader("X-CSRFToken", csrftoken)
        },
        data: JSON.stringify(payload),
        cache: false,
        success: function(response) {
            $("#enroll-counter").text(response.current_enroll_count);
            $(`#enroll-${response.id}`).hide(200);
        },
        error: function(xhr, status, error) {
            alert("An error occured!")
            $(this).removeAttr("disabled");
        }
    });
}

function change_semesterenroll_publishable_state() {
    let enrollment_id = $(this).data('enrollid');
    let payload = {enrollment_id: enrollment_id}
    $.ajax({
        type: "post",
        url: toggle_enrollment_is_publishable_api,
        dataType: "json",
        contentType: "application/json",
        beforeSend: function(xhr){
            $(this).attr("disabled", true);
            xhr.setRequestHeader("X-CSRFToken", csrftoken)
        },
        data: JSON.stringify(payload),
        cache: false,
        success: function(response) {
            if (response.is_publishable) {
                $(`#enroll-${enrollment_id} .student`).removeClass('on-hold');
                $(`#enroll-${enrollment_id} .student button.enroll-hold span`).text('Hold Result');
                $(`#enroll-${enrollment_id} .student button.enroll-hold i`).removeClass('bx-play-circle');
                $(`#enroll-${enrollment_id} .student button.enroll-hold i`).addClass('bx-stop-circle');
            } else {
                $(`#enroll-${enrollment_id} .student`).addClass('on-hold');
                $(`#enroll-${enrollment_id} .student button.enroll-hold span`).text('Publish Result');
                $(`#enroll-${enrollment_id} .student button.enroll-hold i`).removeClass('bx-stop-circle');
                $(`#enroll-${enrollment_id} .student button.enroll-hold i`).addClass('bx-play-circle');
            }
        },
        error: function(xhr, status, error) {
            alert("An error occured!");
            $(this).removeAttr("disabled");
        }
    });
}

// Create PrevPoint via Excel
function uploadExcel(excel_file) {
    let excel_form = new FormData
    excel_form.append("excel", excel_file)
    $.ajax({
        type: "post",
        url: create_session_prevpoint_api,
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

// Add new registration
function createRegistration() {
    const payload = {
        registration_no: $('#new_entry_registration').val()
    }
    if (payload) {
        $.ajax({
            url: add_new_entry_to_semester_api,
            contentType: "application/json",
            type: "POST",
            beforeSend: function(xhr){
                $("#new_entry_alert").hide();
                $("#new_entry_add_button").attr("disabled", true)
                xhr.setRequestHeader("X-CSRFToken", csrftoken)
            },
            data: JSON.stringify(payload),
            cache: false,
            success: function(response){
                showInfo('new_entry_alert', `New registration for ${payload.registration_no} under this semester has been added successfully. Reloading...`);
                setTimeout(()=>{
                    location.reload();
                }, 2000)
            },
            error: function(xhr,status,error_thrown){
                try {
                    showError('new_entry_alert', xhr.responseJSON.details);
                } catch (error) {
                    showError('new_entry_alert', error_thrown);
                }
                $("#new_entry_add_button").removeAttr("disabled");
            }
        })
    }
}

// Committee Section

function load_committee_radios(e) {
    $.ajax({
        type: "get",
        url: committe_radio_html_api + `?name=${e.target.value}`,
        contentType: 'application/json',
        success: function (response) {
            $("#committeeModal .user-list").html(response.html);
        }
    });
}

function add_committee_member() {
    let data = {
        user_pk: parseInt($("input[name='adminIdRadios']:checked").val()),
        member_type: $("#memberTypeSelect").val(),
    }
    $.ajax({
        type: "POST",
        url: add_committee_member_api,
        dataType: "json",
        contentType: "application/json",
        beforeSend: function(xhr){
            $("#addCommitteeAlert").hide();
            $("#addCommitteeBtn").attr("disabled", true)
            xhr.setRequestHeader("X-CSRFToken", csrftoken)
        },
        data: JSON.stringify(data),
        cache: false,
        success: function(response) {
            showInfo('addCommitteeAlert', "Added successfully");
        },
        error: function(xhr, status, _error) {
            try {
                showError("addCommitteeAlert", JSON.stringify(xhr.responseJSON));
            } catch (error) {
                showError("updateSemesterAlert", _error);
            }
        },
        complete: function() {
            $("#addCommitteeBtn").removeAttr("disabled");
        }
    });
}

$(document).ready(function () {
    showDevModal("committeeModal")
    $("#createCourseAddBtn").on('click', createCourse);
    $("#render-tabulation-btn").on('click', renderTabulation);
    $(".part-x-marks").on('keyup', function(){
        let final_input = $(this).attr('id') + "Final";
        $(`#${final_input}`).val($(this).val());
    });
    $("#selectionConfirmBtn").on('click', updateDropcourse);
    $(".btn-check").on("change", function(){
        let checked_status = $(this).prop("checked");
        let course_id = $(this).attr("id");
        let if_existing_drop_course = $(this).hasClass('existing');
        if (checked_status) {
            if (DropCourses.indexAtRemlist(course_id) >= 0) {
                DropCourses.deleteXremoval(course_id);
            }
            // if a course is not in the semester drop course, add to addlist
            if (!if_existing_drop_course) {
                DropCourses.add2addition(course_id)
            }
        } else {
            if (DropCourses.indexAtAddlist(course_id) >= 0) {
                DropCourses.deleteXaddition(course_id);
            }
            // if a course is already present in the semester drop course, add to removelist
            if (if_existing_drop_course) {
                DropCourses.add2removal(course_id)
            }
            
            
        }
        console.log("addlist:");
        console.log(DropCourses.addition);
        console.log("remlist:");
        console.log(DropCourses.removal);
        if (DropCourses.is_empty()) {
            $("#selectionConfirmBtn").attr('disabled', true);
        } else {
            $("#selectionConfirmBtn").removeAttr("disabled");
        }
    });
    // change running status button
    $("#confirm-change-btn").on('click', change_running_status);
    // delete semester
    $("#confirm-del-btn").on('click', delete_semester);
    // update semester 
    $("#update-semester-btn").on('click', updateSemester);
    $(".delete-enroll").on('click', delete_semesterenroll);
    $(".enroll-hold").on('click', change_semesterenroll_publishable_state);
    // prevpoint export
    $("#process-excel-btn").on('click', function() {
        excel_file = $("#excelFile")[0].files
        if (excel_file.length > 0) {
            uploadExcel(excel_file[0]);
        } else {
            alert("Please choose an excel file!");
        }
    })
    // new registration
    $("#new_registration_add_button").on('click', createRegistration)
    // Committee
    $("#adminSearchInp").on('keyup', load_committee_radios);
    $("#adminSearchInp").on('click', load_committee_radios);
    $("#addCommitteeBtn").on('click', add_committee_member);
});