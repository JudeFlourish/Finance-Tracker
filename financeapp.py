# Expense Tracker
# entry point only, the app itself is in the finance_tracker package
#
#   uv run python financeapp.py
#   or: uv run flask --app financeapp run --debug

from dotenv import load_dotenv

from finance_tracker import create_app

# read .env before the app is built, so its settings are used
# (flask run does this by itself, python financeapp.py does not)
load_dotenv()

app = create_app()

if __name__ == "__main__":
    # debug=True so the server restarts by itself when I change the code
    app.run(debug=True)
