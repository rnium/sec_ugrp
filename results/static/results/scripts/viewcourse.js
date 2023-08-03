function showNotification(msg) {
    const elem = document.getElementById('notificationModal')
    const toastBody = document.getElementById('modal-body');
    toastBody.innerText = msg;
    const mBootstrap = new bootstrap.Modal(elem);
    mBootstrap.show()
}


function activateProfileCard() {
    $(".profile-link").on("mouseover", function() {
        $(this).next(".profile-card").show(200)
    })
    $(".profile-link").on("mouseout", function() {
        $(this).next(".profile-card").hide(200)
    })
}

function prepareInputs(record) {
    const InpObj = {
        partAcode: `<input type="text" class="code-inp" ${record.part_A_code ? `value="${record.part_A_code}"` : ``} >`,
        partBcode: `<input type="text" class="code-inp" ${record.part_B_code ? `value="${record.part_B_code}"` : ``} >`,
        partAscore: `<input type="text" class="score-inp ${record.part_A_score == null ? 'empty' : ''}" ${record.part_A_score != null ? `value="${record.part_A_score}"` : ''} >`,
        partBscore: `<input type="text" class="score-inp ${record.part_B_score == null ? 'empty' : ''}" ${record.part_B_score != null ? `value="${record.part_B_score}"` : ''}>`,
        inCourseScore: `<input type="text" class="score-inp ${record.incourse_score == null ? 'empty' : ''}" ${record.incourse_score != null ? `value="${record.incourse_score}"` : ''}>`,
    }
    return InpObj;
}

function render_rows(response) {
    let rows = ""
    for (record of response) {
        let inputs = prepareInputs(record);
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
                            ${inputs.partAcode}
                        </td>
                        <td class="inp-con">
                            ${inputs.partAscore}
                        </td>
                        <td class="code-inp-con">
                            ${inputs.partBcode}
                        </td>
                        <td class="inp-con">
                            ${inputs.partBscore}
                        </td>
                        <td class="inp-con">
                            ${inputs.inCourseScore}
                        </td>
                        <td class="text-info">
                            40
                        </td>
                        <td class="">Pending</td>
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
                            <th>Part A [30]</th>
                            <th>Part B Code</th>
                            <th>Part B [30]</th>
                            <th>In Course [30]</th>
                            <th>In Course [40]</th>
                            <th>Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rows}        
                    </tbody>
                </table>`;

    $("#tableContainer").html(table);
    $("#tablePlaceholder").hide(0, ()=>{
        $("#scoreBoard").show(0, activateProfileCard)
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
            console.log(prepareInputs(response[0]).partBcode);
        },
        error: function(xhr, status, error) {
            alert(error)
        }
    });
}


$(document).ready( function() {
    loadCourseResults()
})