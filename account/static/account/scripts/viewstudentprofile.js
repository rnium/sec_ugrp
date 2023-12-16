// Delete
function delete_student() {
    let showAlert = (msg)=>{
        $("#deleteStudentModal .alert").text(msg)
        $("#deleteStudentModal .alert").show()
    }
    let password = $(`#deleteStudentModal input[type="password"]`).val().trim()
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
            url: delete_student_api,
            dataType: "json",
            contentType: "application/json",
            beforeSend: function(xhr){
                $("#confirm-del-btn").attr("disabled", true)
                $("#deleteStudentModal .alert").hide()
                xhr.setRequestHeader("X-CSRFToken", csrftoken)
            },
            data: JSON.stringify(payload),
            cache: false,
            success: function(response) {
                $('#deleteStudentModal .alert').removeClass('alert-warning');
                $('#deleteStudentModal .alert').addClass('alert-info');
                showAlert("Deleted")
                setTimeout(()=>{
                    window.location.href = response.session_url;
                }, 1000)
            },
            error: function(xhr, status, error) {
                showAlert(xhr.responseJSON.details)
                $("#confirm-del-btn").removeAttr('disabled');
            }
        });
    }
}

// Change Session
function change_session() {
    let showAlert = (msg)=>{
        $("#migrateSessionModal .alert").text(msg)
        $("#migrateSessionModal .alert").show()
    }
    let password = $(`#migrateSessionModal input[type="password"]`).val().trim()
    let session_id = parseInt($("#new_session_selection").val());
    if (password.length == 0) {
        showAlert("Please enter your password");
        return;
    }
    if (isNaN(session_id)) {
        showAlert("Select a session");
        return;
    } else {
        $("#change_session_alert").hide();
    }
    payload = {
        password: password,
        session_id: session_id,
        keep_records: true
    }
    if (! $("#keepRecordsSwitch").prop("checked")) {
        payload.keep_records = false;
    }
    
    if (payload) {
        $.ajax({
            type: "post",
            url: change_session_api,
            dataType: "json",
            contentType: "application/json",
            beforeSend: function(xhr){
                $("#confirm_change_session").attr("disabled", true)
                $("#migrateSessionModal .alert").hide()
                xhr.setRequestHeader("X-CSRFToken", csrftoken)
            },
            data: JSON.stringify(payload),
            cache: false,
            success: function(response) {
                $('#migrateSessionModal .alert').removeClass('alert-danger');
                $('#migrateSessionModal .alert').addClass('alert-info');
                showAlert("Colmplete")
                setTimeout(()=>{
                    location.reload();
                }, 1000)
            },
            error: function(xhr, status, error) {
                showAlert(xhr.responseJSON.details)
                $("#confirm_change_session").removeAttr('disabled');
            }
        });
    }
}

// Stats

function initiate_chart(data) {
    let grades = Object.keys(data.classes);
    let counts = [];
    let bgColors = [];
    for (let grade of grades) {
        counts.push(data.classes[grade])
        if (grade == data.letter_grade) {
            bgColors.push("rgb(5, 194, 112)")
        } else {
            bgColors.push("rgba(0, 150, 155, 0.9)")
        }
    }
    console.log(counts);
    // Chart creation
    const ctx = document.getElementById('cgpaChart').getContext('2d');
    const cgpaChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: grades,
            datasets: [{
                label: 'Total Obtained',
                data: counts,
                backgroundColor: bgColors, // Blue color for bars
                borderColor: 'rgba(54, 162, 235, 1)', // Border color
                borderWidth: 0,
                borderRadius:5,
            }]
        },
        options: {
            scales: {
                x: {
                    display: false,
                    ticks: {
                        display: false
                    },
                    grid: {
                        display: false,
                    }
                },
                y: {
                    display: false,
                    ticks: {
                        display: false
                    },
                    grid: {
                        display: false,
                    }
                }
            },
            plugins: {
                legend: {
                    display: false, // Hide the legend (labels)
                }
            }
        }
    });
}

function get_student_stats() {
    $.ajax({
        type: "get",
        url: student_stats_api,
        contentType: "application/json",
        cache: false,
        success: function(response) {
            $('#position-num').text(response.position);
            $('#position-suffix').text(response.position_suffix);
            initiate_chart(response)
        }
    });
}




$(document).ready(function () {
    get_student_stats();
    $("#confirm-del-btn").on('click', delete_student);
    $("#confirm_change_session").on('click', change_session);
});
