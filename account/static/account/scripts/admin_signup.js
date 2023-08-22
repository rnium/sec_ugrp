const showError = (msg) => {
    $("#signupAlert").removeClass('alert-info');
    $("#signupAlert").addClass('alert-warning');
    $("#signupAlert").text(msg);
    $("#signupAlert").show();
}

function getFormData() {
    data = {};
    let first_name = $("#firstNameInput").val().trim();
    let last_name = $("#lastNameInput").val().trim();
    let password = $("#passwordInput").val().trim();
    let password_retype = $("#passwordInputRepeat").val().trim();
    if (first_name.length == 0) {
        showError("Please Enter First Name")
        return false;
    }
    if (password.length < 8) {
        showError("Password must be at least 8 characters long")
        return false;
    }
    if (password != password_retype) {
        showError("Passwords does not matches")
        return false;
    } else {
        $("#signupAlert").hide(); 
    }
    data.first_name = first_name;
    data.password = password;
    if (last_name.length > 0) {
        data.last_name = last_name;
    }
    return data;
}

function performSignnup() {
    payload = getFormData();
    console.log(payload);
    return;
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
    $("#create-ac-btn").on('click', performSignnup);
});