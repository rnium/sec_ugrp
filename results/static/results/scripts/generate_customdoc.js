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
            insertList();
            var link = response.url;
            if (link) {
                var newTab = window.open(link, '_blank');
                newTab.focus();
            } else {
                console.error('No link found in the API response.');
            }
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

function insertList() {
    $.ajax({
        type: "GET",
        url: customdoc_list_api,
        contentType: false,
        processData: false,
        success: function (response) {
            console.log(response);
            $("#docsModal .modal-body").html(response.html);
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