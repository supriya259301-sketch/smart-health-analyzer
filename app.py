import os
from flask import Flask, render_template, request, redirect, session, jsonify
from dotenv import load_dotenv
from openai import OpenAI

# ---------------- ENV ----------------
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------------- APP SETUP ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)

app.secret_key = "secret123"

# ---------------- DATABASE ----------------
users = {}
history = {}
appointments = []

# ---------------- BP ANALYSIS ----------------
def analyze_bp(sys, dia):
    if sys > 180 or dia > 120:
        return "Hypertensive Crisis", "Critical"
    elif sys >= 140 or dia >= 90:
        return "Hypertension Stage 2", "High"
    elif sys >= 130 or dia >= 80:
        return "Hypertension Stage 1", "Moderate"
    elif sys >= 120:
        return "Elevated", "Moderate"
    else:
        return "Normal", "Low"

# ---------------- DIET LOGIC (FIXED) ----------------
def get_diet(age, condition):
    if age < 18:
        return "Milk, fruits, and protein-rich diet"

    elif 18 <= age <= 30:
        if "Hypertension" in condition:
            return "Low salt diet, avoid junk food, exercise daily"
        else:
            return "Balanced diet with fruits and protein"

    elif 30 < age <= 50:
        return "Low sugar, low salt diet with vegetables"

    else:
        return "Light diet, more fruits, low oil, regular checkups"

# ---------------- HOME ----------------
@app.route("/")
def home():
    return redirect("/login")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        if email in users and users[email]["password"] == password:
            session["user"] = email
            return redirect("/dashboard")

    return render_template("login.html")

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]

        users[email] = {
            "name": request.form["name"],
            "password": request.form["password"],
            "premium": False
        }

        session["temp_user"] = email
        return redirect("/profile")

    return render_template("register.html")

# ---------------- PROFILE ----------------
@app.route("/profile", methods=["GET","POST"])
def profile():
    if request.method == "POST":

        email = session.get("temp_user")

        if not email:
            return redirect("/login")

        users[email]["age"] = int(request.form["age"])
        users[email]["gender"] = request.form["gender"]
        users[email]["address"] = request.form["address"]

        session.pop("temp_user", None)

        return redirect("/login")

    return render_template("profile.html")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        sys = int(request.form["sys"])
        dia = int(request.form["dia"])
        symptoms = request.form.getlist("symptoms")

        condition, risk = analyze_bp(sys, dia)

        # 🔥 USER DATA FETCH
        user = users.get(session["user"], {})

        age = user.get("age", 25)
        gender = user.get("gender", "male")

        # 🔥 DIET APPLY
        diet = get_diet(age, condition)

        # 🔥 SAVE REPORT
        session["report"] = {
            "sys": sys,
            "dia": dia,
            "condition": condition,
            "risk": risk,
            "symptoms": symptoms,
            "age": age,
            "gender": gender,
            "diet": diet
        }

        history.setdefault(session["user"], []).append({
            "sys": sys,
            "dia": dia
        })

        return redirect("/report")

    return render_template("dashboard.html", premium=session.get("premium"))

# ---------------- REPORT ----------------
@app.route("/report")
def report():
    return render_template("report.html", data=session.get("report"))

# ---------------- SUBSCRIPTION ----------------
@app.route("/subscribe")
def subscribe():
    return render_template("subscribe.html", premium=session.get("premium"))

@app.route("/activate-premium")
def activate():
    user = session.get("user")

    if not user:
        return redirect("/login")

    users[user]["premium"] = True
    session["premium"] = True

    return redirect("/dashboard")

# ---------------- DOCTORS ----------------
@app.route("/doctors")
def doctors():
    return render_template("doctors.html", premium=session.get("premium"))

# ---------------- BOOK APPOINTMENT ----------------
@app.route("/book", methods=["POST"])
def book():
    if not session.get("premium"):
        return redirect("/subscribe")

    appointments.append({
        "user": session.get("user"),
        "doctor": request.form["doctor"]
    })

    return "Appointment Booked Successfully ✅"

# ---------------- HISTORY ----------------
@app.route("/history-data")
def history_data():
    data = history.get(session.get("user"), [])

    return jsonify({
        "labels": list(range(1, len(data) + 1)),
        "sys": [d["sys"] for d in data],
        "dia": [d["dia"] for d in data]
    })

# ---------------- CHATBOT ----------------
@app.route("/chatbot")
def chatbot():
    return render_template("chatbot.html")

# ---------------- AI CHAT ----------------
@app.route("/ask-ai", methods=["POST"])
def ask_ai():
    question = request.form.get("msg", "")

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a simple health assistant. Give short safe advice."},
                {"role": "user", "content": question}
            ]
        )

        answer = response.choices[0].message.content

    except:
        q = question.lower()

        if "bp" in q:
            answer = "Maintain low salt diet and check BP daily."
        elif "diet" in q:
            answer = "Eat fruits, vegetables and avoid junk food."
        else:
            answer = "Consult a doctor for proper advice."

    return jsonify({"reply": answer})
@app.route("/thankyou")
def thankyou():
    return render_template("thankyou.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)