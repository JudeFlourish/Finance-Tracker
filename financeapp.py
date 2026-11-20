# Expense Tracker
# entry point only, the app itself is in the finance_tracker package
#
#   uv run python financeapp.py
#   or: uv run flask --app financeapp run --debug

from finance_tracker import create_app

app = create_app()

if __name__ == "__main__":
    # debug=True so the server restarts by itself when I change the code
    app.run(debug=True)
