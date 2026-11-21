"""
app.py
-------
Flask backend for the Stock Portfolio Analyzer, with user accounts.
Works with a portfolio export from any broker/stock app (Groww, Zerodha,
Upstox, Angel One, etc.), or with holdings typed in manually / extracted
from a screenshot via in-browser OCR.

Auth routes:
  GET/POST /register        -> create an account
  GET/POST /login           -> log in
  GET      /logout          -> log out

Core routes:
  GET  /                    -> Dashboard (all stock predictions)
  GET  /portfolio           -> Portfolio upload/analysis page
  POST /api/upload_portfolio -> Accepts a broker CSV export; saves it to the
                                 logged-in user's profile (if logged in)
  POST /api/upload_portfolio_manual -> Accepts holdings as JSON (from the
                                 screenshot-OCR review table, or manual entry)
  GET  /api/my_portfolio    -> Returns the logged-in user's saved analysis
  GET  /api/predictions     -> JSON: predictions for all supported stocks
  GET  /api/stock/<symbol>  -> JSON: prediction + price history for one stock
  GET  /api/metrics         -> JSON: model performance metrics
"""

import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user,
)

import db
from model.predictor import get_predictor
from model.portfolio import parse_portfolio_csv, analyze_portfolio, holdings_list_to_df, manual_entries_to_df
from model.chatbot import get_response as get_chat_response

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024  # 2 MB upload limit
app.secret_key = os.environ.get("SECRET_KEY", "college-project-dev-key-change-me")

db.init_db()
predictor = get_predictor()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.unauthorized_handler
def unauthorized():
    # API routes (called via fetch) need JSON, not a redirect to an HTML page
    if request.path.startswith("/api/"):
        return jsonify({"error": "Not logged in"}), 401
    return redirect(url_for("login", next=request.path))


class User(UserMixin):
    def __init__(self, row):
        self.id = str(row["id"])
        self.username = row["username"]
        self.email = row["email"]


@login_manager.user_loader
def load_user(user_id):
    row = db.get_user_by_id(user_id)
    return User(row) if row else None


# ---------------------- Pages ----------------------

@app.route("/")
def dashboard():
    return render_template("index.html", symbols=predictor.list_symbols())


@app.route("/portfolio")
def portfolio_page():
    return render_template("portfolio.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("portfolio_page"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not username or not email or not password:
            flash("Please fill in all fields.", "error")
            return render_template("register.html")
        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template("register.html")

        user_row, error = db.create_user(username, email, password)
        if error:
            flash(error, "error")
            return render_template("register.html")

        login_user(User(user_row))
        return redirect(url_for("portfolio_page"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("portfolio_page"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user_row = db.get_user_by_username(username)
        if user_row and db.verify_password(user_row, password):
            login_user(User(user_row))
            next_page = request.args.get("next")
            return redirect(next_page or url_for("portfolio_page"))

        flash("Incorrect username or password.", "error")
        return render_template("login.html")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("dashboard"))


# ---------------------- API ----------------------

@app.route("/api/predictions")
def api_predictions():
    return jsonify(predictor.predict_all())


@app.route("/api/stock/<symbol>")
def api_stock(symbol):
    pred = predictor.predict_symbol(symbol)
    if pred is None:
        return jsonify({"error": f"Symbol '{symbol}' not supported"}), 404
    history = predictor.get_history(symbol)
    return jsonify({"prediction": pred, "history": history})


@app.route("/api/metrics")
def api_metrics():
    return jsonify(predictor.metrics)


@app.route("/api/upload_portfolio", methods=["POST"])
def api_upload_portfolio():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    try:
        portfolio_df = parse_portfolio_csv(file, predictor.list_symbols())
        result = analyze_portfolio(portfolio_df, predictor)

        saved = False
        if current_user.is_authenticated:
            db.save_holdings(int(current_user.id), portfolio_df)
            saved = True

        result["saved_to_profile"] = saved
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/my_portfolio")
@login_required
def api_my_portfolio():
    saved = db.get_saved_holdings(int(current_user.id))
    if not saved:
        return jsonify({"holdings": [], "summary": None, "empty": True})

    portfolio_df = holdings_list_to_df(saved, predictor.list_symbols())
    result = analyze_portfolio(portfolio_df, predictor)
    result["empty"] = False
    result["last_uploaded_at"] = saved[0]["uploaded_at"]
    return jsonify(result)


@app.route("/api/upload_portfolio_manual", methods=["POST"])
def api_upload_portfolio_manual():
    """Accepts holdings as JSON (from the screenshot-OCR review table, or
    any manual entry flow) instead of a CSV file."""
    data = request.get_json(silent=True) or {}
    entries = data.get("holdings", [])
    if not entries:
        return jsonify({"error": "No holdings provided"}), 400

    try:
        portfolio_df = manual_entries_to_df(entries, predictor.list_symbols())
        if portfolio_df.empty:
            return jsonify({"error": "Couldn't read any valid holdings from that input"}), 400

        result = analyze_portfolio(portfolio_df, predictor)

        saved = False
        if current_user.is_authenticated:
            db.save_holdings(int(current_user.id), portfolio_df)
            saved = True

        result["saved_to_profile"] = saved
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/auth_status")
def api_auth_status():
    if current_user.is_authenticated:
        return jsonify({"logged_in": True, "username": current_user.username})
    return jsonify({"logged_in": False})


@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "")
    api_key = data.get("api_key") or os.environ.get("GEMINI_API_KEY", "")
    reply = get_chat_response(message, predictor, api_key=api_key)
    return jsonify({"reply": reply})


@app.route("/api/set_gemini_key", methods=["POST"])
def api_set_gemini_key():
    data = request.get_json(silent=True) or {}
    key = data.get("api_key", "").strip()
    if key:
        os.environ["GEMINI_API_KEY"] = key
        return jsonify({"success": True, "message": "Gemini API key configured successfully."})
    return jsonify({"error": "Empty API key provided"}), 400


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
