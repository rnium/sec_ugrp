function setNavCookie(value) {
    let date = new Date()
    date.setTime(date.getTime() + (3600 * 1000 * 24 * 7))
    let expires = "expires=" + date.toUTCString();
    console.log(expires);
    let path = "path=\\"
    document.cookie = `nav=${value};${expires};${path}`; 
}


function activate_menu_btn() {
    $("#menu").on('click', function() {
        if ($('.navbar').hasClass('active')) {
            $("main").css("margin-left", "100px");
            $(".nav-link span").hide();
            $(".navbar").removeClass("active");
            setNavCookie("minimized");
        } else {
            $("main").css("margin-left", "250px");
            $(".nav-link span").show(200);
            $(".navbar").addClass("active");
            setNavCookie("active");
        }
    })
}





$(document).ready(function () {
    activate_menu_btn()    
});