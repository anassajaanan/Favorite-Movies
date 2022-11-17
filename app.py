from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os

# =========TMDB============
API_KEY = "791c66e93914be2d8672bd6569a00712"
tmdb_endpoint = "https://api.themoviedb.org/3/search/movie"



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

Bootstrap(app)
# ========flask_wtforms====================


class UpdateForm(FlaskForm):
    rating = StringField('Your rating out of 10 e.g 7.5',
                         validators=[DataRequired()])
    review = StringField('Your review', validators=[DataRequired()])
    done = SubmitField(label='Done')


class AddForm(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()])
    add_movie = SubmitField('Add Movie')
# ==========create a model=============


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(250), nullable=False, unique=True)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(500), nullable=True)
    img_url = db.Column(db.String(500), nullable=False, unique=True)

    def __repr__(self):
        return f'<Title is : {self.title}>'
with app.app_context():
    db.create_all()

@app.route("/")
def home():
    movies = Movie.query.order_by(Movie.rating).all()
    all_movies = Movie.query.order_by(Movie.rating.desc()).all()
    for i in range(len(all_movies)):
        film = Movie.query.filter_by(title=all_movies[i].title).first()
        film.ranking = i+1
        db.session.commit()
    return render_template("index.html", movies=movies)


@app.route('/edit', methods=['POST', 'GET'])
def edit():
    id = request.args['id']
    form = UpdateForm()
    if form.validate_on_submit():
        new_reting = form.rating.data
        new_review = form.review.data
        movie = Movie.query.get(id)
        movie.rating = new_reting
        movie.review = new_review
        db.session.commit()
        return redirect('/')
    return render_template('edit.html', form=form)


@app.route('/delete', methods=['POST', 'GET'])
def delete():
    id = request.args['id']
    movie = Movie.query.get(id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/add', methods=['POST', 'GET'])
def add():
    add_form = AddForm()
    if add_form.validate_on_submit():
        new_movie_title = add_form.title.data
        response = requests.get(url=tmdb_endpoint, params={
                                "api_key": API_KEY, "query": new_movie_title, })
        data = response.json()["results"]
        return render_template('select.html', movies=data)
    return render_template('add.html', add_form=add_form)


@app.route('/add_film', methods=['POST', 'GET'])
def add_film():
    film_id = request.args['id']
    tmdb_film_endpoint = f"https://api.themoviedb.org/3/movie/{film_id}"
    film_response = requests.get(
        url=tmdb_film_endpoint, params={"api_key": API_KEY})
    data = film_response.json()
    title = data['title']
    img_url = "https://image.tmdb.org/t/p/w500" + data['poster_path']
    year = data['release_date'].split('-')[0]
    description = data['overview']
    new_movie = Movie(title=title, year=year,
                      description=description, img_url=img_url)
    db.session.add(new_movie)
    db.session.commit()
    cuurent_movie = Movie.query.filter_by(title=title).first()
    id = cuurent_movie.id
    return redirect(url_for('edit', id=id))


if __name__ == '__main__':
    app.run()
