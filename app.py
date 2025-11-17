# pylint: disable=missing-module-docstring,missing-function-docstring,invalid-name,superfluous-parens

import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from datetime import datetime
from html import escape

DATA_FILE = "expenses.json"


def load_expenses():
    """Load expenses from a local JSON file."""
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_expenses(expenses):
    """Save expenses list to local JSON file."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(expenses, f)


def generate_index_page():
    """Read HTML template and inject expense rows."""
    with open("templates/index.html", "r", encoding="utf-8") as f:
        template = f.read()

    expenses = load_expenses()
    rows = ""
    for exp in expenses:
        rows += (
            "<tr>"
            f"<td>{escape(exp['date'])}</td>"
            f"<td>{escape(exp['description'])}</td>"
            f"<td>{float(exp['amount']):.2f}</td>"
            f"<td><a href='/delete-expense?id={escape(str(exp['id']))}'>Delete</a></td>"
            "</tr>"
        )

    return template.replace("<!--EXPENSE_ROWS-->", rows)


def validate_expense(description, amount_str, date_str):
    """Basic input validation for description, amount, date."""
    errors = []

    description = description.strip()
    if not description:
        errors.append("Description is required.")

    try:
        amount = float(amount_str)
        if amount <= 0:
            errors.append("Amount must be positive.")
    except ValueError:
        errors.append("Amount must be a number.")
        amount = 0.0

    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        errors.append("Date must be in YYYY-MM-DD format.")

    return errors, {"description": description, "amount": amount, "date": date_str}


class ExpenseTrackerHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the expense tracker."""

    def do_GET(self):
        if self.path == "/" or self.path.startswith("/index"):
            page = generate_index_page()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(page.encode("utf-8"))

        elif self.path.startswith("/static/"):
            file_path = self.path.lstrip("/")
            if os.path.exists(file_path):
                self.send_response(200)
                if file_path.endswith(".css"):
                    self.send_header("Content-Type", "text/css")
                else:
                    self.send_header("Content-Type", "text/plain")
                self.end_headers()
                with open(file_path, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, "Static file not found")

        elif self.path.startswith("/delete-expense"):
            query = urlparse(self.path).query
            params = parse_qs(query)
            expense_id = params.get("id", [None])[0]
            if expense_id is not None:
                expenses = load_expenses()
                expenses = [e for e in expenses if str(e["id"]) != str(expense_id)]
                save_expenses(expenses)

            self.send_response(302)
            self.send_header("Location", "/")
            self.end_headers()

        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        if self.path == "/add-expense":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            fields = parse_qs(body)

            description = fields.get("description", [""])[0]
            amount = fields.get("amount", [""])[0]
            date = fields.get("date", [""])[0]

            errors, expense = validate_expense(description, amount, date)
            if not errors:
                expenses = load_expenses()
                new_id = (max((e["id"] for e in expenses), default=0) + 1)
                expense["id"] = new_id
                expenses.append(expense)
                save_expenses(expenses)

            self.send_response(302)
            self.send_header("Location", "/")
            self.end_headers()
        else:
            self.send_error(404, "Not Found")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    server = HTTPServer(("", port), ExpenseTrackerHandler)
    print(f"Server running on port {port}")
    server.serve_forever()
