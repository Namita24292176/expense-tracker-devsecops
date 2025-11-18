# pylint: disable=missing-module-docstring,missing-function-docstring,invalid-name,superfluous-parens

import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from datetime import datetime
from html import escape

# ----- Paths & data file -----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "expenses.json")
TEMPLATE_FILE = os.path.join(BASE_DIR, "templates", "index.html")
STATIC_DIR = os.path.join(BASE_DIR, "static")


def load_expenses():
    """Load expenses from a local JSON file."""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        # If file is corrupted, reset it
        return []


def save_expenses(expenses):
    """Save expenses list to local JSON file."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(expenses, f)


def generate_index_page():
    """Read HTML template and inject expense rows."""
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
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

    def _set_common_headers(self, status=200, content_type="text/html; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        # Simple security headers
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()

    def do_GET(self):
        if self.path == "/" or self.path.startswith("/index"):
            page = generate_index_page()
            self._set_common_headers(200, "text/html; charset=utf-8")
            self.wfile.write(page.encode("utf-8"))

        elif self.path.startswith("/static/"):
            # Serve static files from the static directory safely
            rel_path = self.path.lstrip("/")
            # Prevent path traversal
            if not rel_path.startswith("static/"):
                self.send_error(403, "Forbidden")
                return

            file_path = os.path.join(BASE_DIR, rel_path)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                if file_path.endswith(".css"):
                    content_type = "text/css"
                elif file_path.endswith(".js"):
                    content_type = "application/javascript"
                else:
                    content_type = "application/octet-stream"

                self._set_common_headers(200, content_type)
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

            # For now, always redirect back to home (could show errors later)
            self.send_response(302)
            self.send_header("Location", "/")
            self.end_headers()
        else:
            self.send_error(404, "Not Found")


if __name__ == "__main__":
    # AWS (and most PaaS) will inject a PORT environment variable
    port = int(os.environ.get("PORT", 5000))
    server_address = ("0.0.0.0", port)  # Bind to all interfaces for cloud hosting
    server = HTTPServer(server_address, ExpenseTrackerHandler)
    print(f"Server running on port {port}")
    server.serve_forever()
