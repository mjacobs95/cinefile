import json
import requests
import pandas as pd

from pandas import json_normalize

# https://developer.themoviedb.org/reference/movie-credits

class DataLoader:

    headers = {
        "accept": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJhZWM3YWNhODc2YWRlMDJhMmVmNDA4YTRiYmJjZWJhYiIsInN1YiI6IjY1OTk4MjY4YmQ1ODhiMDBmMTA5ODc3ZCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.48ZXeBnj37icJ7QkGHkS-1K67k97wENsDHZwX-1WyA0"
        }

    def __init__(self, actor_lim = 10, movie_lim = 20):

        self.actor_lim = actor_lim
        self.movie_lim = movie_lim

        return
    

    def query(self, url, key):

        response = requests.get(url, headers = self.headers)
        data = json.loads(response.text).get(key)

        return data



    def search_movie(self, name = 'jaws'):

        url = "https://api.themoviedb.org/3/search/movie?query={}&include_adult=false&language=en-US&page=1".format(name)
        top_result = self.query(url, 'results')[0]

        return {k: top_result[k] for k in ('id', 'title', 'release_date')}
    

    def search_actor(self, name = 'richard dreyfuss'):

        url = "https://api.themoviedb.org/3/search/person?query={}&include_adult=false&language=en-US&page=1".format(name)
        top_result = self.query(url, 'results')[0]

        return {k: top_result[k] for k in ('id', 'name')}
    

    def get_movie_credits(self, movie_id = 578):

        url = "https://api.themoviedb.org/3/movie/{}/credits".format(movie_id)
        results = self.query(url, 'cast')[:self.actor_lim]

        return [{k:subdict[k] for k in ('id', 'name', 'character')} for subdict in results]
    

    def get_actor_credits(self, person_id = 3037):

        url = "https://api.themoviedb.org/3/person/{}/movie_credits".format(person_id)
        results = self.query(url, 'cast')
        results = sorted(results, key=lambda d: d.get('popularity', 1), reverse = True)[:self.movie_lim]

        return [{k:subdict[k] for k in ('id', 'title', 'release_date', 'popularity', 'character')} for subdict in results]




    

    


if __name__ == '__main__':

    a = DataLoader()

    print(a.search_actor())







