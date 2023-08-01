function showNotification(msg) {
    const elem = document.getElementById('notificationModal')
    const toastBody = document.getElementById('modal-body');
    toastBody.innerText = msg;
    const mBootstrap = new bootstrap.Modal(elem);
    mBootstrap.show()
}

const saveBtn = document.getElementById("save-btn")
saveBtn.addEventListener('click', ()=>{
    // do some saving stuff
    showNotification("Saved Successfully!")
})

$(document).ready( function() {
    $(".profile-link").on("mouseover", function() {
        $(this).next(".profile-card").show(200)
    })
    $(".profile-link").on("mouseout", function() {
        $(this).next(".profile-card").hide(200)
    })
})