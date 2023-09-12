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




$(document).ready(function () {
    $("#confirm-del-btn").on('click', delete_student);
});
