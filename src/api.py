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

    def __init__(self, actor_lim = 5, movie_lim = 10):
        """Initialises the object. 

        Args:
            actor_lim (int, optional): API limit on n actors returned per movie. Defaults to 5.
            movie_lim (int, optional): API limit on n movies returned per actor Defaults to 10.
        """

        self.actor_lim = actor_lim
        self.movie_lim = movie_lim

        return
    

    def query(self, url, key):
        """General API querying function.

        Args:
            url (str): API endpoint.
            key (str): Dictionary key to get data.

        Returns:
            dict: Query response. 
        """

        response = requests.get(url, headers = self.headers)
        data = json.loads(response.text).get(key)

        return data



    def search_movie(self, name = 'jaws'):
        """Specialised API method for finding a movie. 

        Args:
            name (str, optional): Movie name. Defaults to 'jaws'.

        Returns:
            dict: Data for top result. 
        """

        url = "https://api.themoviedb.org/3/search/movie?query={}&include_adult=false&language=en-US&page=1".format(name)
        top_result = self.query(url, 'results')[0]

        return {k: top_result[k] for k in ('id', 'title', 'release_date')}
    

    def search_actor(self, name = 'richard dreyfuss'):
        """Specialised API method for finding an actor. 

        Args:
            name (str, optional): Actor name. Defaults to 'richard dreyfuss'.

        Returns:
            dict: Data for top result.
        """

        url = "https://api.themoviedb.org/3/search/person?query={}&include_adult=false&language=en-US&page=1".format(name)
        top_result = self.query(url, 'results')[0]

        return {k: top_result[k] for k in ('id', 'name')}
    

    def get_movie_credits(self, movie_id = 578):
        """Get actors associated with a movie. 

        Args:
            movie_id (int, optional): TMDB unique movie ID. Defaults to 578.

        Returns:
            list: List of dictionaries, one for each actor.
        """

        url = "https://api.themoviedb.org/3/movie/{}/credits".format(movie_id)
        results = self.query(url, 'cast')[:self.actor_lim]

        return [{k:subdict[k] for k in ('id', 'name', 'character')} for subdict in results]
    

    def get_actor_credits(self, person_id = 3037):
        """Get movies associated with an actor.

        Args:
            person_id (int, optional): TMDB unique actor ID. Defaults to 3037.

        Returns:
            list: List of dictionaries, one for each movie. 
        """

        url = "https://api.themoviedb.org/3/person/{}/movie_credits".format(person_id)
        results = self.query(url, 'cast')
        results = sorted(results, key=lambda d: d.get('popularity', 1), reverse = True)[:self.movie_lim]

        return [{k:subdict[k] for k in ('id', 'title', 'release_date', 'popularity', 'character')} for subdict in results]




    

    


if __name__ == '__main__':

    a = DataLoader()

    print(a.search_actor())







