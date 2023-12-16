def navbarContext(request):
    nav = request.COOKIES.get("nav", "active")
    context = {}
    if nav == "active":
        context['is_navActive'] = True
    return context

def themeContext(request):
    nav = request.COOKIES.get("theme", "light")
    context = {}
    if nav == "light":
        context['is_lightMode'] = True
    return context