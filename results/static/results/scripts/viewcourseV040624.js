// I know it's bad code :| Reviewing after a year

const SEC_GRADING_SCHEMA = {
    "A+": {"min": 80, "max":100, "grade_point":4.0},
    "A": {"min": 75, "max":79.999, "grade_point":3.75},
    "A-": {"min": 70, "max":74.999, "grade_point":3.50},
    "B+": {"min": 65, "max":69.999, "grade_point":3.25},
    "B": {"min": 60, "max":64.999, "grade_point":3.00},
    "B-": {"min": 55, "max":59.999, "grade_point":2.75},
    "C+": {"min": 50, "max":54.999, "grade_point":2.50},
    "C": {"min": 45, "max":49.999, "grade_point":2.25},
    "C-": {"min": 40, "max":44.999, "grade_point":2.00},
    "F": {"min": 0, "max":39.999, "grade_point":0.00}
};

const SEC_GRADING_SCHEMA_CARRY = {
    "A+": {"min": 80, "max":100, "grade_point":4.0},
    "A": {"min": 75, "max":79.999, "grade_point":3.75},
    "A-": {"min": 70, "max":74.999, "grade_point":3.50},
    "B+": {"min": 65, "max":69.999, "grade_point":3.25},
    "B": {"min": 60, "max":64.999, "grade_point":3.00},
    "B-": {"min": 55, "max":59.999, "grade_point":2.75},
    "C+": {"min": 50, "max":54.999, "grade_point":2.50},
    "C": {"min": 45, "max":49.999, "grade_point":2.25},
    "C-": {"min": 40, "max":44.999, "grade_point":2.00},
    "F": {"min": 0, "max":39.999, "grade_point":0.00}
};

function calculateLetterGrade(obtainedScore, maxMarks, is_carry=false) {
    if (obtainedScore === null || obtainedScore === undefined) {
        return null;
    }
    const score = (obtainedScore / maxMarks) * 100;
    const grading_schema = is_carry ? SEC_GRADING_SCHEMA_CARRY : SEC_GRADING_SCHEMA;
    for (const [LG, schema] of Object.entries(grading_schema)) {
        if (schema.min <= score && score <= schema.max) {
            return LG;
        }
    }
    return null;
}

function roundUpPointFive(num) {
    var numInt = Math.floor(num);
    if ((num - numInt) >= 0.5) {
        return numInt + 1;
    } else {
        return num;
    }
}

function calculateGradePoint(obtainedScore, maxMarks, is_carry=false) {
    if (obtainedScore === null || obtainedScore === undefined) {
        return null;
    }
    const score = (obtainedScore / maxMarks) * 100;
    const grading_schema = is_carry ? SEC_GRADING_SCHEMA_CARRY : SEC_GRADING_SCHEMA;
    for (const schema of Object.values(grading_schema)) {
        if (schema.min <= score && score <= schema.max) {
            return schema.grade_point;
        }
    }
    return null;
}



function showModal(id) {
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
            $(`#${alertContainer}`).hide()
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


function showNotification(msg) {
    const elem = document.getElementById('notificationModal')
    const toastBody = document.getElementById('modal-body');
    toastBody.innerText = msg;
    const mBootstrap = new bootstrap.Modal(elem);
    mBootstrap.show()
}

function convertFloat(num) {
    if (num === null || isNaN(num)) {
        return 0;
    }
    
    if (Number.isInteger(num)) { // Check if the number is already an integer
        return num;
    } else if (typeof num === 'number') {
        const decimal = num.toFixed(1); // Get the number rounded to one decimal place
        const lastDigit = decimal.charAt(decimal.length - 1); // Get the last character of the decimal
        if (lastDigit === "0") {
            return parseInt(decimal); // If the last digit is 0, return the integer value
        } else {
            return parseFloat(num.toFixed(2)); // Otherwise, return the original floating point number
        }
    } else {
        return 0; // Return 0 for any other non-numeric input
    }
}

function check_input(inp_id) {
    inp_selector = `#${inp_id}`
    let score_raw = $(inp_selector).val();
    let marks = $(inp_selector).data('max');
    if (score_raw.length > 0) {
        let score = Number(score_raw);
        if (isNaN(score)) {
            $(inp_selector).removeClass("empty")
            $(inp_selector).addClass("error")
            return false
        } else {
            if (score > marks) {
                $(inp_selector).removeClass("empty")
                $(inp_selector).addClass("error")
                return false
            } else {
                $(inp_selector).removeClass("error")
                $(inp_selector).removeClass("empty")
                return true
            }
        }
    } else {
        $(inp_selector).removeClass("error")
        $(inp_selector).addClass("empty")
        return null
    }
}

function validate_inputs() {
    inp_fields = $(".score-inp");
    for (let index = 0; index < inp_fields.length; index++) {
        let element = inp_fields[index].id;
        check_input(element)
    }
    let error_fields = $(".error");
    if (error_fields.length > 0) {
        $(`#${error_fields[0].id}`).focus()
        return false
    } else {
        return true
    }
}


function processData() {
    let dataset = {}
    // first: score input field values
    let inp_fields = $(".score-inp");
    $.each(inp_fields, function (indexInArray, valueOfElement) { 
        const elem_id = valueOfElement.id;
        const elem_selector = `#${elem_id}`;
        const registration = $(elem_selector).data('registration')
        const value = $(elem_selector).val()
        let score = null;
        if (value.length > 0) {
            let score_number = Number(value);
            if (!isNaN(score_number)) {
                score = score_number;
            }
        }
        const partA_id = `part-A-${registration}`;
        const partB_id = `part-B-${registration}`;
        const inCourse_id = `incourse-raw-${registration}`;
        // create the entry for the registration_no
        if (!(registration in dataset)) {
            dataset[registration] = {}
        }

        if (elem_id == partA_id) {
            dataset[registration]['part_A_score'] = score;
        } else if (elem_id == partB_id) {
            dataset[registration]['part_B_score'] = score;
        } else if (elem_id == inCourse_id) {
            dataset[registration]['incourse_score'] = score;
        }
    });
    
    return dataset
}


function processLabcourseData() {
    let dataset = {}
    let inp_fields = $(".total-inp");
    $.each(inp_fields, function (indexInArray, valueOfElement) { 
        const elem_id = valueOfElement.id;
        const elem_selector = `#${elem_id}`;
        const registration = $(elem_selector).data('registration')
        const value = $(elem_selector).val()
        let score = null;
        if (value.length > 0) {
            let score_number = Number(value);
            if (!isNaN(score_number)) {
                score = score_number;
            }
        }
        // create the entry for the registration_no
        if (!(registration in dataset)) {
            dataset[registration] = {}
        }
        dataset[registration]['total_score'] = score;
    });
    
    return dataset
}



function updateAndGetTotalMarks(registration) {
    let a_score = parseFloat($(`#part-A-${registration}`).val().trim());
    let b_score = parseFloat($(`#part-B-${registration}`).val().trim());
    let incourse_score = parseFloat($(`#incourse-raw-${registration}`).val().trim());
    if ((!isNaN(a_score)) | (!isNaN(b_score)) | (!isNaN(incourse_score))) {
        let total = 0;
        if (!isNaN(a_score)) {
            let partA_actual = (course_part_A_marks_final/course_partA_marks) * a_score;
            total += partA_actual;
        }
        if (!isNaN(b_score)) {
            let partB_actual = (course_part_B_marks_final/course_partB_marks) * b_score;
            total += partB_actual;
        }
        if (!isNaN(incourse_score)) {
            total += incourse_score;
        }
        total = convertFloat(total);
        if (total > course_total_marks) {
            $(`#total-${registration}`).text("Invalid");
            $(`#total-${registration}`).addClass('pending');
            $(`#letter-grade-${registration}`).addClass('pending');
            $(`#letter-grade-${registration}`).text('--');
            $(`#grade-point-${registration}`).text('--');
        } else {
            $(`#total-${registration}`).text(total);
            $(`#total-${registration}`).removeClass("pending");
            $(`#letter-grade-${registration}`).removeClass("pending");
        }
        return roundUpPointFive(total);
    } else {
        $(`#total-${registration}`).text("Pending");
        $(`#total-${registration}`).addClass('pending');
        return null;
    }
}


function updateLG(registration, total=null, isLabCourse=true, iscarry=false) {
    let total_score = total;
    if (isLabCourse) {
        total_score = parseFloat($(`#total-inp-${registration}`).val().trim());
        total_score = roundUpPointFive(total_score);
    }
    if (total_score && !isNaN(total_score)) {
        console.log(total_score);
        let total = convertFloat(total_score);
        let letter_grade = calculateLetterGrade(total, course_total_marks, iscarry);
        let grade_point = calculateGradePoint(total, course_total_marks, iscarry);
        $(`#letter-grade-${registration}`).removeClass('pending');
        $(`#letter-grade-${registration}`).text(letter_grade);
        $(`#grade-point-${registration}`).text(grade_point);
    } else {
        console.log('adsa');
        $(`#grade-point-${registration}`).text("---");
        $(`#letter-grade-${registration}`).text('---');
        $(`#letter-grade-${registration}`).addClass('pending');
    }
}

function activateScoreInputs() {
    $(".score-inp").on('keyup', function(){
        let registration = $(this).data('registration');
        let iscarry = $(this).data('iscarry')
        const inp_id = $(this).attr('id');
        // update input class based on values
        check_input(inp_id)
        // update total marks after all other checkings
        let total = updateAndGetTotalMarks(registration)
        updateLG(registration, total, false, iscarry);
    })
    $(".score-inp").on('keydown', function(event) {
        if (event.key === 'Enter') {
            let r = parseInt($(this).data('row'));
            let c = $(this).data('col');
            event.shiftKey ? r -= 1 : r += 1;
            const $myInput = $(`[data-row="${r}"][data-col="${c}"]`);
            $myInput.focus();
            const tempValue = $($myInput).val();;
            $myInput.val('');
            $myInput.val(tempValue);
        }
    })

}

function activateTotalScoreInput() {
    $(".score-inp").on('keyup', function(){
        let registration = $(this).data('registration');
        const iscarry = $(this).data('iscarry');
        const inp_id = $(this).attr('id');
        check_input(inp_id)
        updateLG(registration, null, true, iscarry)
    })
    $(".score-inp").on('keydown', function(event) {
        if (event.key === 'Enter') {
            let r = parseInt($(this).data('row'));
            let c = $(this).data('col');
            event.shiftKey ? r -= 1 : r += 1;
            const $myInput = $(`[data-row="${r}"][data-col="${c}"]`);
            $myInput.focus();
            const tempValue = $($myInput).val();;
            $myInput.val('');
            $myInput.val(tempValue);
        }
    })
}

function generateRowElements(record, idx) {
    const registration = record.student.registration;
    const name = record.student.name;
    const partAscore = record.part_A_score;
    const partBscore = record.part_B_score;
    const incourseScore = record.incourse_score;
    const total_score = record.total_score;
    const letter_grade = record.letter_grade;
    const grade_point = record.grade_point;
    const is_drop_course = record.is_drop_course;
    let totalContainer = "";
    let lgContainer = "";
    let gpContainer = "";
    if (total_score != null) {
        totalContainer = `<td data-registration=${registration} data-iscarry=${is_drop_course} class="total-score themetext" id="total-${registration}">${convertFloat(total_score)}</td>`
    } else {
        totalContainer = `<td data-registration=${registration} data-iscarry=${is_drop_course} id="total-${registration}" class="total-score themetext pending">Pending</td>`
    }
    if (letter_grade != null) {
        lgContainer = `<td data-registration=${registration} class="total-score themetext" id="letter-grade-${registration}">${letter_grade}</td>`
    } else {
        lgContainer = `<td data-registration=${registration} id="letter-grade-${registration}" class="total-score themetext pending">---</td>`
    }
    if (grade_point != null) {
        gpContainer = `<td data-registration=${registration} class="themetext" id="grade-point-${registration}">${grade_point}</td>`
    } else {
        gpContainer = `<td data-registration=${registration} id="grade-point-${registration}" class="themetext">---</td>`
    }
    
    const elements = {
        partAcode: `<input type="text" data-iscarry=${is_drop_course} data-registration=${registration} id="code-part-A-${registration}" class="code-inp" ${record.part_A_code ? `value="${record.part_A_code}"` : ``} ${is_running_semester ? '': "disabled"}>`,
        partBcode: `<input type="text" data-iscarry=${is_drop_course} data-registration=${registration} id="code-part-B-${registration}" class="code-inp" ${record.part_B_code ? `value="${record.part_B_code}"` : ``} ${is_running_semester ? '': "disabled"}>`,
        partAscore: `<input type="text" readonly onfocus="this.removeAttribute('readonly');" name="r${idx}-c${0}" data-row="${idx}" data-col="${0}" data-iscarry=${is_drop_course} data-max="${course_partA_marks}" id="part-A-${registration}" data-registration=${registration} ${partAscore != null ? `value="${partAscore}" class="score-inp"` : 'class="score-inp empty"'} ${is_running_semester ? '': "disabled"}>`,
        partBscore: `<input type="text" readonly onfocus="this.removeAttribute('readonly');" name="r${idx}-c${1}" data-row="${idx}" data-col="${1}" data-iscarry=${is_drop_course} data-max="${course_partB_marks}" id="part-B-${registration}" data-registration=${registration} ${partBscore != null ? `value="${partBscore}" class="score-inp"` : 'class="score-inp empty"'} ${is_running_semester ? '': "disabled"}>`,
        inCourseScore: `<input type="text" readonly onfocus="this.removeAttribute('readonly');" name="r${idx}-c${2}" data-row="${idx}" data-col="${2}" data-iscarry=${is_drop_course} data-max="${course_incourse_marks}" id="incourse-raw-${registration}" data-registration=${registration} ${incourseScore != null ? `value="${incourseScore}" class="score-inp incourse-score"` : 'class="score-inp incourse-score empty"'} ${is_running_semester ? '': "disabled"}>`,
        TotalScoreInp: `<input type="text" readonly onfocus="this.removeAttribute('readonly');" name="r${idx}-c${3}" data-row="${idx}" data-col="${3}" data-iscarry=${is_drop_course} data-max="${course_total_marks}" id="total-inp-${registration}" data-registration=${registration} ${total_score != null ? `value="${total_score}" class="score-inp total-inp"` : 'class="score-inp empty total-inp"'} ${is_running_semester ? '': "disabled"}>`,
        totalContainer: totalContainer,
        lgContainer: lgContainer,
        gpContainer: gpContainer,
        name: name
    }
    return elements;
}

function render_rows_theoryCourse(response) {
    let rows = ""
    for (let i = 0; i < response.length; ++i) {
        let record = response[i];
        let fields = generateRowElements(record, i);
        let row_class = record.is_drop_course ? 'drop_course' : '';
        let row = `<tr class="${row_class}">
                        <td class="student-info">
                            <a class="profile-link" style="cursor: pointer" data-courseresid="${record.id}">${record.student.registration}</a>
                        </td>
                        <td class="inp-con">
                            ${fields.partAscore}
                        </td>
                        <td class="inp-con">
                            ${fields.partBscore}
                        </td>
                        <td class="inp-con">
                            ${fields.inCourseScore}
                        </td>
                        ${fields.totalContainer}
                        ${fields.lgContainer}
                        ${fields.gpContainer}
                    </tr>`;
        rows += row;
    }
    return rows;
}

function render_rows_labCourse(response) {
    let rows = ""
    for (let i = 0; i < response.length; ++i) {
        let record = response[i];
        let fields = generateRowElements(record, i);
        let row_class = record.is_drop_course ? 'drop_course' : '';
        let row = `<tr class="${row_class}">
                        <td class="student-info">
                            <a class="profile-link" style="cursor: pointer" data-courseresid="${record.id}">${record.student.registration}</a>
                        </td>
                        <td class="student-name">${fields.name}</td>
                        <td class="inp-con">
                            ${fields.TotalScoreInp}
                        </td>
                        ${fields.gpContainer}
                        ${fields.lgContainer}
                    </tr>`;
        rows += row;
    }
    return rows;
}

function activateEntryDetails() {
    $(".profile-link").on("click", function() {
        let courseres_id = $(this).data('courseresid');
        let payload = {result_id: courseres_id}
        $.ajax({
            type: "post",
            url: course_result_entry_info_api,
            dataType: "json",
            contentType: "application/json",
            beforeSend: function(xhr){
                $("#entryInfoModal .modal-body").empty();
                $("#entryInfoModal .modal-footer").hide();
                $("#entry-info-loader").show();
                showModal("entryInfoModal");
                xhr.setRequestHeader("X-CSRFToken", csrftoken)
            },
            data: JSON.stringify(payload),
            cache: false,
            success: function(response) {
                $("#entryInfoModal #confirm-entry-del-btn").attr("data-courseres-id", courseres_id);
                $("#entry-info-loader").hide(0, function() {
                    $("#entryInfoModal .modal-body").html(response.content)
                    $("#entryInfoModal .modal-body").show()
                    if (response.semester_running) {
                        $("#entryInfoModal .modal-footer").show()
                    }
                });
            },
            error: function(xhr, status, error) {
                $("#entry-info-loader .loader-info").text(error)
            }
        });
    })
}

function delete_courseresult_entry() {
    if (!confirm("Are you sure to delete this entry?")) {
        return
    }
    let courseres_id = $(this).data('courseres-id');
    let payload = {courseres_id: courseres_id}
    $.ajax({
        type: "post",
        url: course_result_delete_api,
        dataType: "json",
        contentType: "application/json",
        beforeSend: function(xhr){
            $("#confirm-entry-del-btn").attr("disabled", true);
            xhr.setRequestHeader("X-CSRFToken", csrftoken)
        },
        data: JSON.stringify(payload),
        cache: false,
        success: function(response) {
            $("#entry-info-loader .loader-info").text("Done.. Reloading page")
            $("#entryInfoModal .modal-body").empty();
            $("#entryInfoModal .modal-footer").hide();
            $("#entry-info-loader").show();
            setTimeout(()=>{
                location.reload()
            }, 2000)
        },
        error: function(xhr, status, error) {
            alert("An error occured!")
        }
    });
}

function generate_missing_entries() {
    $.ajax({
        type: "post",
        url: generate_missing_entries_api,
        dataType: "json",
        // contentType: "application/json",
        beforeSend: function(xhr){
            $("#generate_missing_btn").attr("disabled", true);
            xhr.setRequestHeader("X-CSRFToken", csrftoken)
        },
        cache: false,
        success: function(response) {
            showNotification("Completed.. please reload");
        },
        error: function(xhr, status, error) {
            $("#generate_missing_btn").attr("disabled", false);
            showNotification("An error occured!");
        }
    });
}

function get_header_row_columns(response) {
    if (is_theory_course) {
        const partA_conv_ratio = convertFloat(course_part_A_marks_final/course_partA_marks);
        const partB_conv_ratio = convertFloat(course_part_B_marks_final/course_partB_marks);
        return `<th>Registration No</th>
                <th>Part A [${course_partA_marks}]
                    <div class="small text-info">conv. ratio: ${partA_conv_ratio}</div>
                </th>
                <th>Part B [${course_partB_marks}]
                    <div class="small text-info">conv. ratio: ${partB_conv_ratio}</div>
                </th>
                <th>In Course [${course_incourse_marks}]</th>
                <th>Total</th>
                <th>LG</th>
                <th>GP</th>`;
    } else {
        return `<th>Registration No</th>
                <th>Student Name</th>
                <th>Total [${course_total_marks}]</th>
                <th>GP</th>
                <th>LG</th>`;
    }
}

function insertTable(response) {
    let rows;
    if (is_theory_course) {
        rows = render_rows_theoryCourse(response);
    } else {
        rows = render_rows_labCourse(response);
    }
    
    let table = `<table>
                    <thead>
                        <tr>
                            ${get_header_row_columns(response)}
                        </tr>
                    </thead>
                    <tbody>
                        ${rows}        
                    </tbody>
                </table>`;

    $("#tableContainer").html(table);
    $("#tablePlaceholder").hide(0, ()=>{
        $("#scoreBoard").show(0, function(){
            if (is_theory_course) {
                activateScoreInputs();
            } else {
                activateTotalScoreInput();
            }
            activateEntryDetails()
        })
    });
}

function loadCourseResults() {
    let load_course_res_api = course_result_api
    if (!isNaN(FROM_SESSION)) {
        load_course_res_api += `?from=${FROM_SESSION}&sem=${FROM_SEMESTER}`;
    }
    $.ajax({
        type: "get",
        url: load_course_res_api,
        data: "data",
        dataType: "json",
        success: function (response) {
            insertTable(response);
        },
        error: function(xhr, status, error) {
            alert(error)
        }
    });
}

function post_data(data) {
    let payload = JSON.stringify(data)
    $.ajax({
        url: update_course_results_api,
        contentType: "application/json",
        type: "POST",
        beforeSend: function(xhr){
            $("#table-save-btn").attr("disabled", true)
            $("#table-save-btn span").text("Saving")
            xhr.setRequestHeader("X-CSRFToken", csrftoken)
        },
        data: payload,
        cache: false,
        success: function(response){
            showNotification("Data Saved Successfully!")
        },
        error: function(xhr,status,error){
            showNotification("Sorry, something went wrong!")
        },
        complete: function(){
            $("#table-save-btn span").text("Save")
            $("#table-save-btn").removeAttr("disabled");
        }
    })
}

function getCourseData() {
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
            $("#editCourseAlert").text("Invalid Input(s), please fill correctly");
            $("#editCourseAlert").show()
            return false;
        }
    } else {
        if (isNaN(totalMarksIn) || isNaN(creditsIn)) {
            $("#editCourseAlert").text("Invalid Input(s), please fill correctly");
            $("#editCourseAlert").show()
            return false;
        }
        partAMarksIn = 0;
        partAMarksInFinal = 0;
        partBMarksIn = 0;
        partBMarksInFinal = 0;
        incourseMarksIn = 0;
    }

    if (courseCodeIn.length == 0 | courseTitleIn.length == 0) {
        $("#editCourseAlert").text("Please fill all the fields");
        $("#editCourseAlert").show()
        return false;
    }
    if (courseCodeArray.length != 2 | isNaN(courseCodeNumber)) {
        $("#editCourseAlert").text("Invalid Course code! Please enter correctly.");
        $("#editCourseAlert").show()
        return false;
    }
    if (((partAMarksInFinal+partBMarksInFinal+incourseMarksIn) > totalMarksIn) && is_theory_course) {
        $("#editCourseAlert").text("Invalid Marks Distribution!");
        $("#editCourseAlert").show()
        return false;
    }
    else {
        $("#editCourseAlert").hide()
    }
    
    data = {
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
    }

    return data;
}

function updateCourse() {
    payload = getCourseData()
    if (payload) {
        $.ajax({
            type: "PATCH",
            url: update_course_api,
            dataType: "json",
            contentType: "application/json",
            beforeSend: function(xhr){
                $("#editCourseAlert").hide()
                $("#updateCourseAddBtn").attr("disabled", true)
                xhr.setRequestHeader("X-CSRFToken", csrftoken)
            },
            data: JSON.stringify(payload),
            cache: false,
            success: function(response) {
                showInfo("editCourseAlert", "Updated successfully")
                setTimeout(()=>{window.location.href = semester_homepage}, 1000)
            },
            error: function(xhr, status, error) {
                $("#updateCourseAddBtn").removeAttr("disabled");
                showError("editCourseAlert", error);
            },
        });
    }
}

function delete_course() {
    let showAlert = (msg)=>{
        $("#deleteCourseModal .alert").text(msg)
        $("#deleteCourseModal .alert").show()
    }
    let password = $(`#deleteCourseModal input[type="password"]`).val().trim()
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
            url: delete_course_api,
            dataType: "json",
            contentType: "application/json",
            beforeSend: function(xhr){
                $("#confirm-del-btn").attr("disabled", true)
                $("#deleteCourseModal .alert").hide()
                xhr.setRequestHeader("X-CSRFToken", csrftoken)
            },
            data: JSON.stringify(payload),
            cache: false,
            success: function(response) {
                $('#deleteCourseModal .alert').removeClass('alert-warning');
                $('#deleteCourseModal .alert').addClass('alert-info');
                showAlert("Deleted Successfully")
                setTimeout(()=>{
                    window.location.href = response.semester_url
                }, 1000)
            },
            error: function(xhr, status, error) {
                showAlert(xhr.responseJSON.details)
                $("#confirm-del-btn").removeAttr('disabled');
            }
        });
    }
}

// add new entry for student
let retaking_courseresult_id = null;
function activate_retake_choices() {
    $(".retake-btn").on('click', function(event){
        if (! $(this).is("checked")) {
            $("#new_entry_add_button").show();
        } 
        let current_id = this.id;
        let all_btns = $(".retake-btn");
        all_btns.each(function() {
            $(this).prop('checked', false);
        })
        $(this).prop('checked', true);
        retaking_courseresult_id = $(this).data("retakingcr");
    })
}

function get_student_retakigs() {
    let reg = $("#new_entry_registration").val();
    let data = {
        registration: parseInt(reg),
    };
    let payload = JSON.stringify(data)
    $.ajax({
        url: student_retakings_api,
        contentType: "application/json",
        type: "POST",
        beforeSend: function(xhr){
            $("#new_entry_alert").hide();
            $("#new_entry_add_button").hide();
            $("#retaking-info").hide(0, ()=>{
                $("#retakings-container").hide(0, ()=>{
                    $("#newentry-loader").show();
                });
            });
            xhr.setRequestHeader("X-CSRFToken", csrftoken)
        },
        data: payload,
        cache: false,
        success: function(response){
            if (response.retaking_courses.length == 0) {
                $("#retaking-info .info-text").text("No Carry Courses");
                $("#retaking-info").show(0);
            }
            else {
                // List all courses
                $("#retakings-container").empty();
                for (retaking of response.retaking_courses) {
                    let elem = `<div class="col-md-4 py-2 m-0">
                                    <input type="checkbox" class="retake-btn btn-check" id="retake-${retaking.courseresult_id}" data-retakingcr="${retaking.courseresult_id}" autocomplete="off">
                                    <label class="btn btn-outline-warning w-100" for="retake-${retaking.courseresult_id}">${retaking.course_code}</label><br>
                                </div>`;
                    $("#retakings-container").append(elem);
                }
                $("#retakings-container").show();
                activate_retake_choices();
            }
        },
        error: function(xhr,status,error){
            try {
                $("#retaking-info .info-text").text(xhr.responseJSON.detail);
            } catch (error_) {
                $("#retaking-info .info-text").text(error);
            }
            $("#retaking-info").show();
        },
        complete: function(){
            $("#newentry-loader").hide(0);
        }
    })
}

function get_entry_data() {
    let registration = parseInt($("#new_entry_registration").val().trim());
    if ( isNaN(registration) || registration.length == 0) {
        showError('new_entry_alert', "Enter valid registration number")
        return false;
    }
    return {
        registration: registration,
    };
}

function addNewEntry() {
    const show_error = msg => {
        showError('new_entry_alert', msg);
    }
    let payload = get_entry_data()
    if (payload) {
        $.ajax({
            url: add_new_entry_to_course_api,
            contentType: "application/json",
            type: "POST",
            beforeSend: function(xhr){
                $("#new_entry_add_button").attr("disabled", true)
                xhr.setRequestHeader("X-CSRFToken", csrftoken)
            },
            data: JSON.stringify(payload),
            cache: false,
            success: function(response){
                location.reload()
            },
            error: function(xhr,status,error_thrown){
                show_error(xhr.responseJSON?.detail || error_thrown || 'Error')
                $("#new_entry_add_button").removeAttr("disabled");
            }
        })
    }
}

// Excel upload
function uploadScoresExcel(excel_file) {
    let excel_form = new FormData
    excel_form.append("excel", excel_file)
    excel_form.append("semester_from", FROM_SEMESTER)
    
    $.ajax({
        type: "post",
        url: process_course_excel_api,
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
            $("#summary_list_container").show(500);
            loadCourseResults();
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

function uploadAndRenderSustDoc(excel_file) {
    let excel_form = new FormData
    excel_form.append("excel", excel_file);
    $.ajax({
        type: "post",
        url: render_course_sustdocs_api,
        data: excel_form,
        contentType: false,
        processData: false,
        beforeSend: function(xhr){
            $("#sustDocRenderBtn").attr("disabled", true);
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
            $("#sustDocRenderBtn").removeAttr("disabled");
        }
    });
}


$(document).ready( function() {
    loadCourseResults()
    $("#table-save-btn").on('click', function(){
        let validated = validate_inputs()
        if (!validated) {
            return;
        } else {
            let data;
            if (is_theory_course) {
                data = processData();
            } else {
                data = processLabcourseData();
            }
            post_data(data)
        }
    })
    
    $("#updateCourseAddBtn").on('click', updateCourse)
    $("#confirm-entry-del-btn").on('click', delete_courseresult_entry)
    $("#confirm-del-btn").on('click', delete_course)
    $("#generate_missing_btn").on('click', generate_missing_entries)
    // new entry registration input
    $("#new_entry_registration").keypress(function(event) {
        if (event.which === 13 || event.keyCode === 13) {
            get_student_retakigs();
        }
    })
    // new entry button
    $("#new_entry_add_button").on('click', addNewEntry)
    // course results excel upload button
    $("#process-excel-btn").on('click', function() {
        excel_file = $("#excelFile")[0].files
        if (excel_file.length > 0) {
            uploadScoresExcel(excel_file[0]);
        } else {
            alert("Please choose an excel file!")
        }
    })
    // sust docs
    $("#sustDocRenderBtn").on('click', function() {
        excel_file = $("#sustDocExcel")[0].files;
        if (excel_file.length > 0) {
            uploadAndRenderSustDoc(excel_file[0]);
        } else {
            alert("Please choose an excel file!");
        }
    })
    // focus reg input of addnewentry
    $("#add-new").on('click', ()=>{
        setTimeout(() => {
            $("#new_entry_registration").focus();
        }, 500);
    })
})