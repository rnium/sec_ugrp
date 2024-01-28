function showDevModal(id) {
    const elem = document.getElementById(id)
    const mBootstrap = new bootstrap.Modal(elem);
    mBootstrap.show()
}

function activateDeptAdminRadio() {
    $("#deptAdminRadio").on("click", function() {
        let checked_status = $(this).prop("checked");
        if (checked_status) {
            $("#deptSelect").removeAttr("disabled");
        } else {
            $("#deptSelect").attr("disabled", "disabled");
        }
    })
    $(".non-dept").on("click", function() {
        let checked_status = $(this).prop("checked");
        if (checked_status) {
            $("#deptSelect").attr("disabled", "disabled");
        } else {
            $("#deptSelect").removeAttr("disabled");
        }
    })
}


function getInvitationData() {
    data = {};
    let to_email = $("#emailInput").val().trim();
    let actype = $("input[name='adminTypeRadios']:checked").val();
    if (to_email.length < 3) {
        $("#invitationModal .alert").text("Please Enter Email")
        $("#invitationModal .alert").show();
        return false;
    } else {
        $("#invitationModal .alert").hide();
        data.to_email = to_email;
    }
    data.actype = actype;
    if (actype === 'dept') {
        let to_user_dept = parseInt($("#deptSelect").val().trim());
        if (isNaN(to_user_dept)) {
            $("#invitationModal .alert").text("Please select a department!");
            $("#invitationModal .alert").show();
            return false;
        }
        else {
            $("#invitationModal .alert").hide();
            data.is_to_user_superadmin = false;
            data.to_user_dept = to_user_dept;
        }
    }
    return data;
}

function sendInvite() {
    payload = getInvitationData();
    if (payload) {
        $.ajax({
            type: "post",
            url: send_staff_signup_token_api,
            dataType: "json",
            contentType: "application/json",
            beforeSend: function(xhr){
                $("#createCourseAlert").hide()
                $("#send-invite").attr("disabled", true)
                xhr.setRequestHeader("X-CSRFToken", csrftoken)
            },
            data: JSON.stringify(payload),
            cache: false,
            success: function(response) {
                $("#invitationModal .alert").removeClass('alert-warning');
                $("#invitationModal .alert").addClass('alert-info');
                $("#invitationModal .alert").text(response['status']);
                $("#invitationModal .alert").show();
            },
            error: function(xhr, status, error) {
                $("#send-invite").attr("disabled", false);
                $("#invitationModal .alert").text(xhr.responseJSON.details);
                $("#invitationModal .alert").show();
            },
        });
    }
}

$(document).ready(function () {
    activateDeptAdminRadio()
    $("#send-invite").on('click', sendInvite)
});