function showError(msg) {
    $("#email-inp-con").hide(50, ()=>{
        $("#error-info-raw").text(msg)
        $("#error-info-con").show(50, ()=>{
            setTimeout(()=>{
                $("#error-info-con").hide(50, ()=>{
                    $("#email-inp-con").show(50)
                })
            }, 3000)
        })
    })
}

function showError2(msg) {
    $("#setup_new_pass_err-raw").text(msg);
    $("#setup_new_pass_err-con").show(50, ()=>{
        setTimeout(()=>{
            $("#setup_new_pass_err-con").hide()
        },3000)
    })
}

function send_mail(btn_id, data) {
    let payload = JSON.stringify(data)
    $.ajax({
        url: send_mail_url,
        contentType: "application/json",
        type: "POST",
        beforeSend: function(xhr){
            $(`#${btn_id}`).text("Sending");
            $(`#${btn_id}`).attr("disabled", true);
            xhr.setRequestHeader("X-CSRFToken", csrftoken)
        },
        data: payload,
        dataType: "json",
        cache: false,
        success: function(response){
            $("#content-con").hide(200, ()=>{
                $("#success-info-con").show(200);
            })
        },
        statusCode: {
            400: function() {
                showError("Email not  sent")
                $(`#${btn_id}`).text("Submit");
                $(`#${btn_id}`).attr("disabled", false)
            },
            404: function() {
                showError("No user found with this email")
                $(`#${btn_id}`).text("Submit");
                $(`#${btn_id}`).attr("disabled", false)
            },
            406: function() {
                showError("Email not verified")
                $(`#${btn_id}`).text("Submit");
                $(`#${btn_id}`).attr("disabled", false)
            },
            409: function() {
                showError("User has no account")
                $(`#${btn_id}`).text("Submit");
                $(`#${btn_id}`).attr("disabled", false)
            },
            503: function() {
                showError("Cannot send email")
                $(`#${btn_id}`).text("Submit");
                $(`#${btn_id}`).attr("disabled", false)
            }
        }
    })
}

function set_new_password(btn_id, data) {
    let payload = JSON.stringify(data)
    $.ajax({
        url: reset_password_api_url,
        contentType: "application/json",
        type: "POST",
        beforeSend: function(xhr){
            $(`#${btn_id}`).attr("disabled", true);
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        },
        data: payload,
        dataType: "json",
        cache: false,
        success: function(response){
            $("#content-con").hide(200, ()=>{
                $("#success-info-con").show(200, ()=>{
                    setTimeout(()=>{
                        window.location.href = login_url
                    }, 3000)
                })
            })
        },
        statusCode: {
            400: function() {
                showError2("No password sent")
                $(`#${btn_id}`).attr("disabled", false)
            },
            404: function() {
                showError2("User not found")
                $(`#${btn_id}`).attr("disabled", false)
            }
        }
    })
}

$("#submit_email_btn").on('click', ()=>{
    let email = $("#email").val()
    if (email.length == 0) {
        $("#email").focus()
    } else {
        data = {"email":email}
        send_mail("submit_email_btn", data)
    }
})


let passtogglers = $(".password-toggle")
for (let toggler of passtogglers) {
    $(`#${toggler.id}`).on('click', function(){
        let inp_id = $(this).data('inp')
        if ($(`#${inp_id}`).attr('type') == "password") {
            $(`#${inp_id}`).attr('type', 'text')
            $(this).removeClass('bx-hide')
            $(this).addClass('bx-show')
            $(`#${inp_id}`).focus()
        } else {
            $(`#${inp_id}`).attr('type', 'password')
            $(this).removeClass('bx-show')
            $(this).addClass('bx-hide')
            $(`#${inp_id}`).focus()
        }
    })
}

$("#create-new-pass-btn").on('click', ()=>{
    let pass1 = $("#password0").val()
    let pass2 = $("#password1").val()
    if (pass1.length == 0 && pass2.length == 0) {
        showError2("Please Enter New Password")
    } else {
        if (pass1 != pass2) {
            showError2("Passwords doesn't match")
        } else {
            data = {'new_password':pass1}
            set_new_password("create-new-pass-btn", data)
        }
    }

})