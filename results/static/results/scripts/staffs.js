function showDevModal(id) {
    const elem = document.getElementById(id)
    const mBootstrap = new bootstrap.Modal(elem);
    mBootstrap.show()
}

function activateDeptAdminRadio() {
    $("#gridRadios2").on("click", function() {
        let checked_status = $(this).prop("checked");
        if (checked_status) {
            $("#deptSelect").removeAttr("disabled");
        } else {
            $("#deptSelect").attr("disabled", "disabled");
        }
    })
    $("#gridRadios1").on("click", function() {
        let checked_status = $(this).prop("checked");
        if (checked_status) {
            $("#deptSelect").attr("disabled", "disabled");
        } else {
            $("#deptSelect").removeAttr("disabled");
        }
    })
}

$(document).ready(function () {
    activateDeptAdminRadio()
});