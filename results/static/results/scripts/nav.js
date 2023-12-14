function setNavCookie(value) {
    let date = new Date()
    let path = "path=/"
    date.setTime(date.getTime() + (3600 * 1000 * 24 * 7))
    let expires = "expires=" + date.toUTCString();
    let cookiestr = `nav=${value};${expires};${path};sameSite=lax`;
    document.cookie = cookiestr;
}

function setThemeCookie(value) {
    let date = new Date()
    let path = "path=/"
    date.setTime(date.getTime() + (3600 * 1000 * 24 * 7))
    let expires = "expires=" + date.toUTCString();
    let cookiestr = `theme=${value};${expires};${path};sameSite=lax`;
    document.cookie = cookiestr;
}

function themeToggle() {
    if ($("#themeSwitch").is(":checked")) {
        $('body').attr('data-bs-theme', 'dark');
        $('body').removeClass('light');
    } else {
        $('body').attr('data-bs-theme', 'light');
        $('body').addClass('light');
    }
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
    $("#themeSwitch").on('click', function() {
        themeToggle()
        if ($('body').hasClass('light')) {
            setThemeCookie("light");
        } else {
            setThemeCookie("dark");
        }
    });
}





$(document).ready(function () {
    activate_menu_btn()    
});