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

function calculate_Incourse(score) {
    if (score == null) {
        return "--";
    }
    let result = (required_inCourse_marks/course_incourse_marks) * score;
    return convertFloat(result);
}

function updateTotalMarks(registration) {
    let a_score = parseFloat($(`#part-A-${registration}`).val().trim());
    let b_score = parseFloat($(`#part-B-${registration}`).val().trim());
    let incourse_score = parseFloat($(`#incourse-converted-${registration}`).text().trim());
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
        // check for incourse marks
        if ($(this).hasClass('incourse-score')) {
            let new_converted_marks = calculate_Incourse($(this).val());
            $(`#incourse-converted-${registration}`).text(new_converted_marks)
            if (isNaN(new_converted_marks) | (new_converted_marks > required_inCourse_marks) ) {
                $(`#incourse-converted-${registration}`).text("Invalid")
                $(`#incourse-converted-${registration}`).removeClass("text-info");
                $(`#incourse-converted-${registration}`).addClass("text-warning");
            } else {
                $(`#incourse-converted-${registration}`).addClass("text-info");
                $(`#incourse-converted-${registration}`).removeClass("text-warning");
            }
        }
        // update total marks after all other changes
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
        totalContainer = `<td id="total-${registration}">${convertFloat(partAscore+partBscore+required_inCourse_score)}</td>`
    } else {
        totalContainer = `<td id="total-${registration}" class="pending">Pending</td>`
    }
    const elements = {
        partAcode: `<input type="text" data-registration=${registration} class="code-inp" ${record.part_A_code ? `value="${record.part_A_code}"` : ``} >`,
        partBcode: `<input type="text" data-registration=${registration} class="code-inp" ${record.part_B_code ? `value="${record.part_B_code}"` : ``} >`,
        partAscore: `<input type="text" id="part-A-${registration}" data-registration=${registration} ${partAscore != null ? `value="${partAscore}" class="score-inp"` : 'class="score-inp empty"'}  >`,
        partBscore: `<input type="text" id="part-B-${registration}" data-registration=${registration} ${partBscore != null ? `value="${partBscore}" class="score-inp"` : 'class="score-inp empty"'} >`,
        inCourseScore: `<input type="text" id="incourse-raw-${registration}" data-registration=${registration} ${incourseScore != null ? `value="${incourseScore}" class="score-inp incourse-score"` : 'class="score-inp incourse-score empty"'} >`,
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
                        <td class="inp-con">
                            ${fields.partAscore}
                        </td>
                        <td class="code-inp-con">
                            ${fields.partBcode}
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
                            <th>Part A [${course_partA_marks}]</th>
                            <th>Part B Code</th>
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


$(document).ready( function() {
    loadCourseResults()
})