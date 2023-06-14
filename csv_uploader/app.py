import os.path

import polars
from flask import Flask, request, redirect, render_template, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

UPLOADS_DIR = "uploads"
ALLOWED_EXT = "csv"
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///./master.db"
app.secret_key = "mama"
db = SQLAlchemy(app)


def allowed_ext(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() == ALLOWED_EXT

class Upload(db.Model):
    __tablename__ = 'uploads'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    cols = db.Column(db.String)


@app.route("/", methods=["GET"])
def index():
    uploads = db.session.execute(db.select(Upload)).scalars()
    return render_template("index.html", uploads=uploads, style="templates/index.css")


@app.route("/upload", methods=["POST"])
def upload_csv():
    if request.method == "POST":
        if 'file' not in request.files:
            return redirect(request.host_url)

        file = request.files['file']
        if file.filename == '':
            return redirect(request.host_url)

        if file and allowed_ext(file.filename):
            filename = secure_filename(file.filename)
            filedir = os.path.join(UPLOADS_DIR, filename)
            file.save(filedir)
            if db.session.execute(db.select(Upload)
                                          .filter_by(name=filename)) \
                    .scalar_one_or_none() is None:
                try:
                    db.session.add(Upload(name=filename,
                                          cols="".join(polars.read_csv(filedir).columns)))
                except:
                    db.session.add(Upload(name=filename,
                                          cols="Columns Not Present"))
                db.session.commit()
        return redirect(request.host_url)


@app.route("/load", methods=["GET"])
def get_file():
    filename = request.args.get('filename')
    sort_by = request.args.get('sort_by')
    filter_by = request.args.get('filter_by')

    if filename == '':
        return redirect(request.host_url)

    data = polars.read_csv(os.path.join(UPLOADS_DIR, filename))
    if sort_by != '':
        if filter_by != '':
            return render_template("load.html", data=data.filter(eval(filter_by)).sort(sort_by.split()),
                                   filename=filename)
        return render_template("load.html", data=data.sort(sort_by.split()), filename=filename)

    return render_template("load.html", data=data, filename=filename)
