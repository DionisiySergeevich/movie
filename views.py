from pathlib import Path

from flask import Flask, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired, FileAllowed
from werkzeug.utils import secure_filename
from wtforms import StringField, SubmitField, TextAreaField, SelectField, FileField
from wtforms.validators import DataRequired, Optional, length
from datetime import datetime

app = Flask(__name__)
db = SQLAlchemy(app)
app.config["SECRET_KEY"] = "SECRET_KEY"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"
BASEDIR = Path(__file__).parent
UPLOAD_FOLDER = BASEDIR / 'static' / 'images'


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(), nullable=False)
    image = db.Column(db.String(255), nullable=False)
    reviews = db.relationship("Review", back_populates="movie")


db.create_all()


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow())
    score = db.Column(db.Integer, nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey("movie.id", ondelete="CASCADE"))
    movie = db.relationship("Movie", back_populates="reviews")


db.create_all()


class ReviewForm(FlaskForm):
    name = StringField("Ваше имя", validators=[DataRequired(message="Поле не должно быть пустым"),
                       length(max=255, message='Введите заголовок длиной до 255 символов')])
    text = TextAreaField("Текст отзыва", validators=[DataRequired(message="Поле не должно быть пустым")])
    choices = list(map(lambda x: x, range(1, 11)))
    score = SelectField("Оценка", choices=choices)
    submit = SubmitField("Добавить отзыв", validators=[DataRequired(message="Поле не должно быть пустым")])


class AddMovieForm(FlaskForm):
    title = StringField("Ваше имя", validators=[DataRequired(message="Поле не должно быть пустым"),
                                               length(max=255, message='Введите заголовок длиной до 255 символов')])
    description = TextAreaField("Текст отзыва", validators=[DataRequired(message="Поле не должно быть пустым")])
    image = FileField("Изображение", validators=[FileRequired(message="Поле не должно быть пустым"),
                      FileAllowed(['jpg', 'jpeg', 'png'], message="Неверный формат файла")])
    submit = SubmitField("Добавить отзыв", validators=[DataRequired(message="Поле не должно быть пустым")])


@app.route("/")
def index():
    movies = Movie.query.order_by(Movie.id.desc()).all()
    return render_template("index.html", movies=movies)


@app.route( "/movie/<int:id>", methods=["GET", "POST"])
def movie(id):
    movie = Movie.query.get(id)
    if movie.reviews:
        avg_score = round(sum(review.score for review in movie.reviews) / len(movie.reviews), 2)
    else:
        avg_score = 0
    form = ReviewForm(score=10)
    if form.validate_on_submit():
        review = Review()
        review.name = form.name.data
        review.text = form.text.data
        review.score = form.score.data
        review.movie_id = movie.id
        db.session.add(review)
        db.session.commit()
        return redirect(url_for("movie", id=movie.id))
    return render_template("movie.html", movie=movie, avg_score=avg_score, form=form)


@app.route( "/add_movie", methods=["GET", "POST"])
def add_movie():
    form = AddMovieForm()
    movie = Movie()
    if form.validate_on_submit():
        movie.title = form.title.data
        movie.description = form.description.data
        image = form.image.data
        image_name = secure_filename(image.filename)
        UPLOAD_FOLDER.mkdir(exist_ok=True)
        image.save(UPLOAD_FOLDER / image_name)
        movie.image = image_name
        db.session.add(movie)
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("add_movie.html", form=form)


if __name__ == "__main__":
    app.run(debug=True)