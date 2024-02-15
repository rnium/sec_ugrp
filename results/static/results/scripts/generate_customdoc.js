function showModal(id) {
    const elem = document.getElementById(id)
    const mBootstrap = new bootstrap.Modal(elem);
    mBootstrap.show()
}

function renderCustomdoc(excel_file) {
    let excel_form = new FormData
    excel_form.append("file", excel_file)
    $.ajax({
        type: "POST",
        url: generate_customdoc_api,
        data: excel_form,
        contentType: false,
        processData: false,
        beforeSend: function(xhr){
            $("#render-cd-btn").attr("disabled", true)
            $("#render-cd-btn .content").hide(0, ()=>{
                $("#render-cd-btn .spinner").show()
            });
        },
        success: function(response) {
            insertList(() => showModal("docsModal"));
            getStudentDocs(response.reg);
        },
        error: function(xhr, status, error) {
            try {
                alert(xhr.responseJSON.details);
            } catch (error_) {
                alert(error);
            }
        },
        complete: function() {
            $("#render-cd-btn").removeAttr("disabled");
            $("#render-cd-btn .spinner").hide(0, ()=>{
                $("#render-cd-btn .content").show()
            });
        }
    });
}

function getStudentDocs(reg) {
    $.ajax({
        type: "GET",
        url: student_customdocs_api+`?reg=${reg}`,
        contentType: false,
        processData: false,
        beforeSend: function() {
            $("#docsModal .modal-footer").hide(200);
        },
        success: function(response) {
            $("#docsModal .student-docs-detail").html(response.html);
            $("#docsModal .modal-footer").show(200);
        },
        error: function() {
            console.log("Error loading list")
        }

    });
}

function bindBtnEvent() {
    $(".student-reg").on('click', function() {
        let reg = parseInt($(this).attr('data-reg'));
        getStudentDocs(reg);
    })
}

function insertList(callback=null) {
    $.ajax({
        type: "GET",
        url: customdoc_list_api,
        contentType: false,
        processData: false,
        success: function (response) {
            $("#docsModal .modal-body").html(response.html);
            bindBtnEvent();
            if (callback) {
                callback();
            }
        },
        error: function() {
            console.log("Error loading list")
        }

    });
}

$(document).ready(function () {
    insertList();
    $("#render-cd-btn").on('click', function(){
        excel_file = $("#excelInp")[0].files
        if (excel_file.length > 0) {
            renderCustomdoc(excel_file[0]);
        } else {
            alert("Please choose an excel file!");
        }
    });
    
});