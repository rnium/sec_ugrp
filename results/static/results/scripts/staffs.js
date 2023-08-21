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
    $("#superAdminRadio").on("click", function() {
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
    if (actype != 'super') {
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
    } else {
        data.is_to_user_superadmin = true;
    }
    return data;
}

function sendInvite() {
    payload = getInvitationData();
    console.log(payload);
    if (payload) {
        $.ajax({
            type: "post",
            url: create_course_api,
            dataType: "json",
            contentType: "application/json",
            beforeSend: function(xhr){
                $("#createCourseAlert").hide()
                $("#createCourseAddBtn").attr("disabled", true)
                xhr.setRequestHeader("X-CSRFToken", csrftoken)
            },
            data: JSON.stringify(payload),
            cache: false,
            success: function(response) {
                hideModal("newSemesterEntryModal");
                showInfo("createCourseAlert", "New course created successfully! Reloading page in a moments")
                setTimeout(()=>{location.reload()}, 3000)
            },
            error: function(xhr, status, error) {
                $("#createCourseAddBtn").removeAttr("disabled");
                showError("createCourseAlert", error);
            },
        });
    }
}

$(document).ready(function () {
    activateDeptAdminRadio()
    $("#send-invite").on('click', sendInvite)
});