from flask import Flask, redirect, render_template, request
from flask_migrate import Migrate

from extensions import db

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"

db.init_app(app)
migrate = Migrate(app, db)

from models.todo import Todo


@app.route("/")
def home():
    todo = Todo.query.all()
    return render_template("home.html", todo=todo)


@app.route("/new/", methods=["POST"])
def new_task():
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]

        task = Todo(title=title, content=content)

        try:
            db.session.add(task)
            db.session.commit()
            return redirect("/")
        except Exception as e:
            return "an error occured while saving the created task"

    else:
        return "only post is allowed"

@app.route("/edit/<int:id>/", methods=["POST", "GET"])
def update_task(id):
    task = Todo.query.get_or_404(id)
    if request.method == "POST":
        task.title = request.form["title"]
        task.content = request.form["content"]
        db.session.commit()
        return redirect("/")

    else:
        return render_template("edit_tasks.html", task=task)

@app.route("/delete/<int:id>", methods = ["POST"])
def delete_task(id):
    if request.method == "POST":
        task = Todo.query.get_or_404(id)
        db.session.delete(task)
        db.session.commit()
        return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
