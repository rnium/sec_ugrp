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

function activateProfileCard() {
    $(".profile-link").on("mouseover", function() {
        $(this).next(".profile-card").show(200)
    })
    $(".profile-link").on("mouseout", function() {
        $(this).next(".profile-card").hide(200)
    })
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
    // second: Code inputs
    let code_inp_fields = $(".code-inp");
    $.each(code_inp_fields, function (indexInArray, valueOfElement) { 
        const elem_id = valueOfElement.id;
        const elem_selector = `#${elem_id}`;
        const registration = $(elem_selector).data('registration')
        let value = $(elem_selector).val().trim()
        if (value.length == 0) {
            value = null
        }
        const partAcode_id = `code-part-A-${registration}`;
        const partBcode_id = `code-part-B-${registration}`;
        // create the entry for the registration_no
        if (!(registration in dataset)) {
            dataset[registration] = {}
        }
        if (elem_id == partAcode_id) {
            dataset[registration]['part_A_code'] = value;
        } else if (elem_id == partBcode_id) {
            dataset[registration]['part_B_code'] = value;
        }
    });
    
    return dataset
}


function calculate_Incourse(score) {
    if (score == null | isNaN(score)) {
        return "--";
    }
    let result = (required_inCourse_marks/course_incourse_marks) * score;
    return convertFloat(result);
}

function updateTotalMarks(registration) {
    let a_score = parseFloat($(`#part-A-${registration}`).val().trim());
    let b_score = parseFloat($(`#part-B-${registration}`).val().trim());
    let incourse_score;
    if (inCourse_needs_conversion) {
        incourse_score = parseFloat($(`#incourse-converted-${registration}`).text().trim());
    } else {
        incourse_score = parseFloat($(`#incourse-raw-${registration}`).val().trim())
    }
    if ((!isNaN(a_score)) && (!isNaN(b_score)) && (!isNaN(incourse_score))) {
        let total = (a_score + b_score + incourse_score);
        if (total > course_total_marks) {
            $(`#total-${registration}`).text("Invalid");
            $(`#total-${registration}`).addClass('pending');
        } else {
            $(`#total-${registration}`).text(total);
            $(`#total-${registration}`).removeClass("pending");
        }
    } else {
        $(`#total-${registration}`).text("Pending");
        $(`#total-${registration}`).addClass('pending');
    }
}

function activateScoreInputs() {
    $(".score-inp").on('keyup', function(){
        let registration = $(this).data('registration');
        const inp_id = $(this).attr('id');
        // update input class based on values
        check_input(inp_id)
        // check for incourse marks
        if ($(this).hasClass('incourse-score')) {
            let new_converted_marks = calculate_Incourse($(this).val());
            let converted_marks_container = `#incourse-converted-${registration}`;
            $(converted_marks_container).text(new_converted_marks)
            if (isNaN(new_converted_marks) | (new_converted_marks > required_inCourse_marks) ) {
                $(converted_marks_container).text("--")
                $(converted_marks_container).removeClass("text-info");
                $(converted_marks_container).addClass("text-warning");
            } else {
                $(converted_marks_container).addClass("text-info");
                $(converted_marks_container).removeClass("text-warning");
            }
        }
        // update total marks after all other checkings
        updateTotalMarks(registration)
    })
}


function generateRowElements(record) {
    const registration = record.student.registration;
    const partAscore = record.part_A_score;
    const partBscore = record.part_B_score;
    const incourseScore = record.incourse_score;
    const required_inCourse_score = calculate_Incourse(record.incourse_score);
    let totalContainer = "";
    if ((!isNaN(partAscore)) && (!isNaN(partBscore)) && (!isNaN(required_inCourse_score))) {
        totalContainer = `<td data-registration=${registration} class="total-score" id="total-${registration}">${convertFloat(partAscore+partBscore+required_inCourse_score)}</td>`
    } else {
        totalContainer = `<td data-registration=${registration} id="total-${registration}" class="total-score pending">Pending</td>`
    }
    const elements = {
        partAcode: `<input type="text" data-registration=${registration} id="code-part-A-${registration}" class="code-inp" ${record.part_A_code ? `value="${record.part_A_code}"` : ``} ${is_running_semester ? '': "disabled"}>`,
        partBcode: `<input type="text" data-registration=${registration} id="code-part-B-${registration}" class="code-inp" ${record.part_B_code ? `value="${record.part_B_code}"` : ``} ${is_running_semester ? '': "disabled"}>`,
        partAscore: `<input type="text" data-max="${course_partA_marks}" id="part-A-${registration}" data-registration=${registration} ${partAscore != null ? `value="${partAscore}" class="score-inp"` : 'class="score-inp empty"'} ${is_running_semester ? '': "disabled"}>`,
        partBscore: `<input type="text" data-max="${course_partB_marks}" id="part-B-${registration}" data-registration=${registration} ${partBscore != null ? `value="${partBscore}" class="score-inp"` : 'class="score-inp empty"'} ${is_running_semester ? '': "disabled"}>`,
        inCourseScore: `<input type="text" data-max="${course_incourse_marks}" id="incourse-raw-${registration}" data-registration=${registration} ${incourseScore != null ? `value="${incourseScore}" class="score-inp incourse-score"` : 'class="score-inp incourse-score empty"'} ${is_running_semester ? '': "disabled"}>`,
        convertedInCourse: `<td id="incourse-converted-${registration}" class="${ isNaN(required_inCourse_score) ? 'text-warning' : "text-info"}">${required_inCourse_score}</td>`,
        totalContainer: totalContainer
    }
    return elements;
}

function render_rows(response) {
    let rows = ""
    for (record of response) {
        let fields = generateRowElements(record);
        let row = `<tr>
                        <td class="student-info">
                            <a href="#" class="profile-link" data-id="${record.student.registration}">${record.student.registration}</a>
                            <div class="profile-card" id="${record.student.registration}-profile" style="display: none;">
                                <div class="inner">
                                    <img src="${record.student.profile_picture_url}" alt="" class="dp">
                                    <div class="info mt-2">
                                        <div class="name">${record.student.name}</div>
                                        <div class="reg-no">${record.student.registration}</div>
                                        <div class="session"><span class="dept me-1">${record.student.dept.dept}</span><span>${record.student.dept.session_code}</span></div>
                                    </div>
                                </div>
                            </div>
                        </td>
                        <td class="code-inp-con">
                            ${fields.partAcode}
                        </td>
                        <td class="code-inp-con">
                            ${fields.partBcode}
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
                        ${inCourse_needs_conversion ? fields.convertedInCourse : ""}
                        ${fields.totalContainer}
                    </tr>`;
        rows += row;
    }
    return rows;
}

function insertTable(response) {
    let rows = render_rows(response);
    let table = `<table>
                    <thead>
                        <tr>
                            <th>Registration No</th>
                            <th>Part A Code</th>
                            <th>Part B Code</th>
                            <th>Part A [${course_partA_marks}]</th>
                            <th>Part B [${course_partB_marks}]</th>
                            <th>In Course [${course_incourse_marks}]</th>
                            ${inCourse_needs_conversion ? `<th>In Course [${required_inCourse_marks}]</th>` : ``}
                            <th>Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rows}        
                    </tbody>
                </table>`;

    $("#tableContainer").html(table);
    $("#tablePlaceholder").hide(0, ()=>{
        $("#scoreBoard").show(0, function(){
            activateProfileCard()
            activateScoreInputs()
        })
    });
}

function loadCourseResults() {
    $.ajax({
        type: "get",
        url: course_result_api,
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


$(document).ready( function() {
    loadCourseResults()
    $("#table-save-btn").on('click', function(){
        let validated = validate_inputs()
        if (!validated) {
            return;
        } else {
            let data = processData()
            post_data(data)
        }
    })
})