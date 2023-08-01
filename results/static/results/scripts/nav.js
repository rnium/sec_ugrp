function activate_menu_btn() {
    $("#menu").on('click', function() {
        if ($('.navbar').hasClass('active')) {
            $("main").css("margin-left", "100px");
            $(".nav-link span").hide();
            $(".navbar").removeClass("active");
        } else {
            $("main").css("margin-left", "250px");
            $(".nav-link span").show(200);
            $(".navbar").addClass("active");
            
        }
    })
}

$(document).ready(function () {
    activate_menu_btn()    
});