def navbarContext(request):
    nav = request.COOKIES.get("nav", "")
    context = {}
    if nav == "active":
        context['is_navActive'] = True
    return context