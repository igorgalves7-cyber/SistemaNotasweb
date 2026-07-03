from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# -------------------------
# Modelo da Nota
# -------------------------

class Nota(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    numero = db.Column(db.String(20), nullable=False)

    fornecedor = db.Column(db.String(100), nullable=False)

    valor = db.Column(db.Float, nullable=False)

    status = db.Column(db.String(30), default="Recebida")


# cria o banco automaticamente
with app.app_context():
    db.create_all()


# -------------------------
# Dashboard
# -------------------------

@app.route("/")

def dashboard():

    notas = Nota.query.all()

    return render_template("dashboard.html", notas=notas)


# -------------------------
# Receber Nota
# -------------------------

@app.route("/receber", methods=["GET","POST"])

def receber():

    if request.method == "POST":

        numero = request.form["numero"]

        fornecedor = request.form["fornecedor"]

        valor = float(request.form["valor"])

        nova = Nota(
            numero=numero,
            fornecedor=fornecedor,
            valor=valor
        )

        db.session.add(nova)

        db.session.commit()

        return redirect("/")

    return render_template("receber.html")


if __name__ == "__main__":

    app.run(debug=True)