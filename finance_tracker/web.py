"""Small helpers shared by the route modules."""
from flask import redirect, request, url_for


def is_safe_path(target):
    # only paths on this site, like "/edit/3". "//evil.com" and "\\evil.com"
    # are read by browsers as links to another website, so they are refused
    return target.startswith("/") and not target.startswith("//") and "\\" not in target


def redirect_back(default_endpoint, **values):
    """Go back to the page the form came from (the hidden "next" field).

    Falls back to default_endpoint when there is no "next" value or it is
    not a path on this site.
    """
    target = request.form.get("next") or request.args.get("next") or ""
    if is_safe_path(target):
        return redirect(target)
    return redirect(url_for(default_endpoint, **values))
