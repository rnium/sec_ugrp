function showDevModal(id) {
    const elem = document.getElementById(id)
    const mBootstrap = new bootstrap.Modal(elem);
    mBootstrap.show()
}

function activateDeptAdminRadio() {
    $(".dept-admin").on("click", function() {
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
    data.actype = actype == undefined ? 'dept' : actype;
    if (actype === 'dept' || actype === 'head') {
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

// Delete account
function delete_account() {
    let showAlert = (msg)=>{
        $("#deleteUserModal .alert").text(msg)
        $("#deleteUserModal .alert").show()
    }
    let target_email = $(`#deleteUserModal input[type="email"]`).val().trim()
    let password = $(`#deleteUserModal input[type="password"]`).val().trim()
    if (target_email.length == 0) {
        showAlert("Please enter the email of the account to be deleted");
        return
    }
    if (password.length == 0) {
        showAlert("Please enter your password");
        return
    }
    const payload = {
        password: password,
        target_email: target_email
    }
    if (payload) {
        $.ajax({
            type: "post",
            url: delete_admin_account_api,
            dataType: "json",
            contentType: "application/json",
            beforeSend: function(xhr){
                $("#confirm-del-btn").attr("disabled", true)
                $("#deleteUserModal .alert").hide()
                xhr.setRequestHeader("X-CSRFToken", csrftoken)
            },
            data: JSON.stringify(payload),
            cache: false,
            success: function(response) {
                $('#deleteUserModal .alert').removeClass('alert-warning');
                $('#deleteUserModal .alert').addClass('alert-info');
                showAlert("Complete")
                setTimeout(()=>{
                    location.reload();
                }, 1000)
            },
            error: function(xhr, status, error) {
                showAlert(xhr.responseJSON.details)
                $("#confirm-del-btn").removeAttr('disabled');
            }
        });
    }
}

$(document).ready(function () {
    activateDeptAdminRadio()
    $("#send-invite").on('click', sendInvite)
    $("#confirm-del-btn").on('click', delete_account)
});