from os.path import dirname
import random

import pandas as pd

from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

app = FastAPI()

templates = Jinja2Templates(f'{dirname(__file__)}/templates')
films = pd.read_csv(dirname(__file__) + '/data.csv', converters={'genres': eval, 'countries': eval, 'actors': eval})

genres = set()
for genre in films['genres']:
    genres.update(genre)
genres = sorted(genres)

actors = set()
for actor in films['actors']:
    actors.update(actor)
actors = sorted(actors)


@app.get('/', response_class=HTMLResponse)
def get_main_page(request: Request):
    return templates.TemplateResponse('main_page.html', {'request': request})


@app.get('/search_by_genres', response_class=HTMLResponse)
def search_by_genres(request: Request):
    return templates.TemplateResponse(
        'search_by_genres_page.html',
        {'request': request, 'genres': genres, 'start': True}
    )


@app.post('/search_by_genres', response_class=HTMLResponse)
def search_by_genre(request: Request, wanted_genres: set = Form({})):
    matched = films[pd.Series([wanted_genres.issubset(i) for i in films['genres']])]['title'].tolist()
    return templates.TemplateResponse(
        'search_by_genres_page.html',
        {
            'request': request,
            'genres': genres,
            'matched': matched,
            'empty': len(matched) == 0}
    )


@app.get('/search_by_actors', response_class=HTMLResponse)
def search_by_genre(request: Request):
    return templates.TemplateResponse(
        'search_by_actors_page.html', 
        {'request': request, 'actors': actors, 'start': True}
    )


@app.post('/search_by_actors', response_class=HTMLResponse)
def search_by_actors(request: Request, wanted_actors: set = Form({})):
    matched = films[pd.Series([wanted_actors.issubset(i) for i in films['actors']])]['title'].tolist()
    return templates.TemplateResponse(
        'search_by_actors_page.html',
        {
            'request': request,
            'actors': actors,
            'matched': matched,
            'empty': len(matched) == 0}
    )


film_to_guess = ''


@app.get('/guess', response_class=HTMLResponse)
def guess_film(request: Request):
    global film_to_guess
    chosen_actor = random.choice(list(actors))
    film_to_guess = random.choice(films[pd.Series(chosen_actor in i for i in films['actors'])]['title'].tolist())
    sample = random.sample(films[pd.Series(chosen_actor not in i for i in films['actors'])]['title'].tolist(), 3)
    sample.append(film_to_guess)
    random.shuffle(sample)
    return templates.TemplateResponse(
        'guess_page.html',
        {
            'request': request,
            'attempt': True,
            'chosen_actor': chosen_actor,
            'sample': sample
        }
    )


@app.post('/guess', response_class=HTMLResponse)
def guess_film(request: Request, chosen_film: str = Form(...)):
    return templates.TemplateResponse(
        'guess_page.html',
        {
            'request': request,
            'film_to_guess': film_to_guess,
            'answer': chosen_film == film_to_guess
        }
    )
