
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, session
from functools import wraps
import json
import os
from geopy.geocoders import Nominatim

app = Flask(__name__)
app.secret_key = 'supersecretkey123'  # change this in production

USERNAME = 'admin'
PASSWORD = 'iconpcr'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == USERNAME and request.form['password'] == PASSWORD:
            session['logged_in'] = True
            return redirect('/')
        return 'Invalid credentials', 401
    return """
        <form method="post">
          <h2>Login</h2>
          <input type="text" name="username" placeholder="Username"><br>
          <input type="password" name="password" placeholder="Password"><br>
          <input type="submit" value="Login">
        </form>
    """

@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/data")
@login_required
def data():
    with open("installs.json") as f:
        return jsonify(json.load(f))

@app.route("/bulk_import", methods=["POST"])
@login_required
def bulk_import():
    data = request.get_json()
    geolocator = Nominatim(user_agent="iconpcr")
    success, failed = [], []
    for d in data:
        try:
            location = geolocator.geocode(d["address"])
            if location:
                success.append({
                    "institution": d["institution"],
                    "lat": location.latitude,
                    "lng": location.longitude,
                    "date": d["date"]
                })
            else:
                failed.append(d)
        except Exception:
            failed.append(d)
    with open("installs.json", "r") as f:
        existing = json.load(f)
    existing += success
    with open("installs.json", "w") as f:
        json.dump(existing, f, indent=2)
    return jsonify({"success": existing, "failed": failed})

@app.route("/edit", methods=["POST"])
@login_required
def edit():
    i = request.get_json()
    with open("installs.json", "r") as f:
        installs = json.load(f)
    installs[i["index"]].update({
        "institution": i["institution"],
        "address": i["address"],
        "date": i["date"]
    })
    with open("installs.json", "w") as f:
        json.dump(installs, f, indent=2)
    return jsonify(installs)

@app.route("/delete", methods=["POST"])
@login_required
def delete():
    i = request.get_json()["index"]
    with open("installs.json", "r") as f:
        installs = json.load(f)
    installs.pop(i)
    with open("installs.json", "w") as f:
        json.dump(installs, f, indent=2)
    return jsonify(installs)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
