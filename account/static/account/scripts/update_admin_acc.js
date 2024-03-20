function setupAvatar(image_file, registration) {
    let image_form = new FormData
    image_form.append("dp", image_file)
    image_form.append("registration", registration)
    $.ajax({
        type: "post",
        url: set_admin_avatar_api,
        data: image_form,
        contentType: false,
        processData: false,
        error: function(xhr, status, _error) {
            try {
                alert(JSON.stringify(xhr.responseJSON));
            } catch (error) {
                alert(_error);
            }
        },
        complete: function() {
            setTimeout(()=>{
                location.reload()
            }, 1000)
        }
    });
}

function setThemeCookie(value) {
    let date = new Date()
    let path = "path=/"
    date.setTime(date.getTime() + (3600 * 1000 * 24 * 7))
    let expires = "expires=" + date.toUTCString();
    let cookiestr = `theme=${value};${expires};${path};sameSite=lax`;
    document.cookie = cookiestr;
}


function getFormData() {
    let first_name = $("#firstnameInput").val().trim();
    let last_name = $("#lastnameInput").val().trim();
    
    if (first_name.length == 0) {
        alert("Please Enter First Name")
        return false;
    }
    data = {};
    data.first_name = first_name;
    if (last_name.length > 0) {
        data.last_name = last_name;
    }
    return data;
}

function performUpdate() {
    payload = getFormData();
    if (payload) {
        $.ajax({
            type: "patch",
            url: update_admin_account_api,
            dataType: "json",
            contentType: "application/json",
            beforeSend: function(xhr){
                $("#update-ac-btn").attr("disabled", true);
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            },
            data: JSON.stringify(payload),
            cache: false,
            success: function(response) {
                avatar_files = $("#dp")[0].files
                if (avatar_files.length > 0) {
                    setupAvatar(avatar_files[0], response.registration);
                } else {
                    location.reload();
                }
            },
            error: function(xhr, status, _error) {
                $("#update-ac-btn").attr("disabled", false);
                try {
                    alert(xhr.responseJSON.details);
                } catch (error) {
                    alert(_error);
                }
            },
        });
    }
}

$(document).ready(function () {
    $("#update-ac-btn").on('click', performUpdate);
    $("#themeSwitch").on('click', function() {
        themeToggle()
        if ($('body').hasClass('light')) {
            setThemeCookie("light");
        } else {
            setThemeCookie("dark");
        }
    });
});