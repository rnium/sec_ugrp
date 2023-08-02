function getSessionData() {
    let years = $("#yearInput").val().trim();
    let batchInput = $("#batchNoInput").val().trim();
    years = years.split("-")
    let from_year_no = parseInt(years[0])
    let to_year_no = parseInt(years[1])
    let batchNo = parseInt(batchInput)
    if (isNaN(batchNo) | isNaN(from_year_no) | isNaN(to_year_no)) {
        $("#createSessionAlert").text("Invalid Input");
        $("#createSessionAlert").show()
        return false;
    }
    if ((to_year_no % 2000) - (from_year_no % 2000) != 1) {
        $("#createSessionAlert").text("Invalid Session Code");
        $("#createSessionAlert").show()
        return false;
    }
    else {
        $("#createSessionAlert").hide()
    }
    data = {
        "from_year": from_year_no,
        "to_year": to_year_no,
        "batch_no": batchNo,
        "dept": dept_id
    }
    return data;
}

function hideModal(modalId) {
    $(`#${modalId}`).modal('hide');
    
}

function renderAndInsertNewSession(response, containerId) {
    let session = `<div class="col-md-4 p-0">
                        <a href="${response['view_url']}" class="session new d-block shadow-sm text-center p-3 m-1 rounded-3">
                            <div class="session-year fs-4">${response['session_code']}</div>
                            <div class="batch text-info">${response['batch_name']}</div>
                            <i class='bg bx bxs-group'></i>
                        </a>
                    </div>`
    $(`#${containerId}`).prepend(session);
    console.log(session);
}

function createSession() {
    payload = getSessionData()
    if (payload) {
        $.ajax({
            type: "post",
            url: create_session_api,
            dataType: "json",
            contentType: "application/json",
            beforeSend: function(xhr){
                $("#createSessionAlert").hide()
                $("#addSessionBtn").attr("disabled", true)
                xhr.setRequestHeader("X-CSRFToken", csrftoken)
            },
            data: JSON.stringify(payload),
            cache: false,
            success: function(response) {
                $("#addSessionBtn").removeAttr("disabled");
                hideModal("newEntryModal");
                renderAndInsertNewSession(response, "sessionContainer")
            },
            error: function(xhr, status, error) {
                $("#addSessionBtn").removeAttr("disabled");
                $("#createSessionAlert").text(xhr.responseJSON['detail'])
                console.log(xhr);
                $("#createSessionAlert").show()
            },
        });
    }
}

$(document).ready(function () {
    $("#addSessionBtn").on('click', createSession)
});