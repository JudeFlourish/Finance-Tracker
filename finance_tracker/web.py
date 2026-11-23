"""Small helpers shared by the route modules."""
from flask import current_app, redirect, render_template, request, url_for

# the links in the nav bar, as (label, endpoint)
# a link only shows once its route exists, so a new page appears in the
# nav as soon as its route is added
NAV_LINKS = [
    ("Home", "dashboard.home"),
    ("Expenses", "expenses.index"),
    ("Income", "income.list_income"),
    ("Budgets", "budgets.list_budgets"),
]


def nav_links():
    return [(label, endpoint) for label, endpoint in NAV_LINKS
            if endpoint in current_app.view_functions]


def init_app(app):
    # makes nav_links available in every template (used by base.html)
    @app.context_processor
    def add_nav_links():
        return {"nav_links": nav_links()}

    # unknown pages and ids get a page in the app's own layout
    @app.errorhandler(404)
    def not_found(error):
        return render_template("404.html"), 404


def is_safe_path(target):
    # only paths on this site, like "/expenses/". "//evil.com" and "\\evil.com"
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
