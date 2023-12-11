function getFormData() {
    let data = {
        reg_num: $('#RegInput').val(),
        duration: $('#durationInp').val(),
        name: $('#nameInp').val(),
        degree: $('#degreeInput').val(),
        exam_scheduled: $('#examScheduled').val(),
        exam_held: $('#examHeld').val(),
        credits_complete: $('#finalResCredit').val(),
        cgpa: $('#finalResCG').val(),
        letter_grade: $('#finalResLG').val(),
        students_appears: $('#numStudentsAppeared').val(),
        session_degrees_count: $('#degreeCounts').val(),
    }
    for (let key in data) {
        if (data[key].length == 0) {
            alert("All the required fields not filled properly!");
            return false;
        }
    }
    return data;
}

function renderTranscript() {
    let data = getFormData();
    if (data == false) return;
    $.ajax({
        type: "post",
        url: generate_transcript_api,
        data: JSON.stringify(data),
        contentType: "application/json",
        beforeSend: function(xhr){
            xhr.setRequestHeader("X-CSRFToken", csrftoken)
            $("#render-tr-btn").attr("disabled", true)
            $("#render-tr-btn .content").hide(0, ()=>{
                $("#render-tr-btn .spinner").show()
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
            $("#render-tr-btn").removeAttr("disabled");
            $("#render-tr-btn .spinner").hide(0, ()=>{
                $("#render-tr-btn .content").show()
            });
        }
    });
}

$(document).ready(function () {
    $("#render-tr-btn").on('click', renderTranscript);
});