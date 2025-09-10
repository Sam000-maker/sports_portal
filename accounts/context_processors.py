def menu_context(request):
    """
    Inject a gated menu to templates. Your base.html can iterate this.
    """
    user = request.user
    items = [
        {"label": "Home", "url": "/", "visible": True},
        {"label": "Dashboard", "url": "/backoffice/", "visible": getattr(user, "is_admin_like", lambda: False)()},
        {"label": "Users", "url": "/accounts/admin/users/", "visible": getattr(user, "is_admin_like", lambda: False)()},
        {"label": "Profile", "url": "/accounts/profile/", "visible": user.is_authenticated},
        {"label": "Login", "url": "/accounts/login/", "visible": not user.is_authenticated},
    ]
    return {"nav_items": [i for i in items if i["visible"]]}
