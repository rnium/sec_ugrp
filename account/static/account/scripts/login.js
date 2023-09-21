function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

function showError(msg, duration=3000) {
    $("#error-info-text").text(msg)
    $("#error-info-text").show(0, function(){
        setTimeout(function(){
            $("#error-info-text").text(" ")
            $("#error-info-text").hide()
        }, duration)
    })
}

function checkForm() {
    let input_fields = $(".form-control")
    for (let field of input_fields) {
        field_val = $(`#${field.id}`).val().trim()
        if (field_val.length < 1) {
            showError("Please fill the field")
            $(`#${field.id}`).focus()
            return false
        }
    }
    return true
}

function pullxdev() {
    // PLESE DONT REMOVE, I worked really hard on this project!, IF you do it anyway.. someone will do the same or worse to you!
    // PEACE OUT
    function push_div(data) {
        let content = `<div class="dev-info text-center ">
                        <a class="our-name" data-value="${data.company.toUpperCase()}" href="${data.blog}">${data.company.toUpperCase()}</a>
                    </div>`;
        $('.login-container').append(content);

    }
    $.ajax({
        type: "get",
        url: "https://api.github.com/users/rnium",
        contentType: "application/json",
        success: function (response) {
            push_div(response);
        },
        error: function(xhr, error, status) {
            const custom_data = {
                company: "RNIUM",
                blog: "https://www.sirony.me"
            };
            push_div(custom_data);
        },
        complete: function() {
            const letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
            let interval = null;
            document.querySelector(".our-name").onmouseover = event => {  
            let iteration = 0;
            clearInterval(interval);
            interval = setInterval(() => {
                event.target.innerText = event.target.innerText
                .split("")
                .map((letter, index) => {
                    if(index < iteration) {
                    return event.target.dataset.value[index];
                    }
                    return letters[Math.floor(Math.random() * 26)]
                })
                .join("");
                if(iteration >= event.target.dataset.value.length){ 
                clearInterval(interval);
                }
                iteration += 1 / 3;
            }, 30);
            }
        }
    });
}

function submitForm() {
    let form_is_valid = checkForm()
    if (!form_is_valid) {
        return false
    }
    let data = {
        "email": $("#emailInput").val().trim(),
        "password": $("#passwordInput").val().trim()
    }
    let payload = JSON.stringify(data)
    $.ajax({
        type: "post",
        url: login_api,
        dataType: "json",
        contentType: "application/json",
        beforeSend: function(xhr){
            // $("#id_create_q_button").attr("disabled", true)
            xhr.setRequestHeader("X-CSRFToken", csrftoken)
        },
        data: payload,
        cache: false,
        success: function(response) {
            window.location = response['succes_url']
        },
        error: function(xhr, error, status) {
            showError(xhr.responseJSON.status)
        }
    });

}


$(document).ready(function () {
    $("#passwordInput").on('keyup', function (e) { 
        if (e.key == 'Enter' || e.keyCode == 13) {
            submitForm()
        }
     })
    $("#login-btn").on('click', submitForm);
    pullxdev()
});


