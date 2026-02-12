from flask import Blueprint, render_template
from datetime import datetime

landing_bp = Blueprint(
    "landing",
    __name__,
    template_folder="templates",
    url_prefix="/"
)

@landing_bp.route("/")
def home():
    return render_template("landing/index.html", year=datetime.now().year)
