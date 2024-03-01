# Cinephile

## Graphical actor and movie linking software

This project automatically links two movies or two actors via the shortest path of actors and movies it can find. It does this by iteratively making requests to [The Movie Database (TMDB) API](https://developer.themoviedb.org/reference/intro/getting-started) and building a network until the two original nodes are connected. 

### Getting started

1. Clone the repository with `git clone https://github.com/mjacobs95/cinefile.git` and `cd` into it. 
2. Create a new virtual environment with `python -m venv <venv_name>`.
3. Install requirements with `pip install -r requirements.txt`.
4. Visit the [TMDB website](https://developer.themoviedb.org/reference/intro/getting-started) and follow the steps to get authenticated. 
5. Copy your API key and paste it in `headers` in the `DataLoader` class in `src/api.py`.
6. In `src/network.py`, instantiate a `NetworkBuilder` object and run the `main()` method!

### Algorithm

<img src="/images/algo.png" alt="Network building algorithm" width="100"/>

The algorithm in `NetworkBuilder` works by iteratively expanding the network from the two starting nodes. Below is a partially expanded graph with two nodes representing the actor Richard Dreyfuss. 

<img src="/images/1.png" alt="Unresolved Richard Dreyfuss" width="100"/>

The algorithm needs to resolve these two nodes to connect the graph.

<img src="/images/2.png" alt="Resolved Richard Dreyfuss" width="100"/>


