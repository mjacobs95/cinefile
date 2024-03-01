import networkx as nx

from src.network import NetworkBuilder


a = NetworkBuilder()


def test_movie():

    subdict = a.search_movie('jaws')

    assert all([k in subdict.keys() for k in ['id', 'title', 'release_date']])


def test_actor():

    subdict = a.search_actor('richard dreyfuss')

    assert all([k in subdict.keys() for k in ['id', 'name']])


def test_graph():

    assert type(a.G) == nx.Graph


def test_expand():

    n_nodes_0 = len(a.G.nodes())

    a.expand_all(resolve = True)

    n_nodes_1 = len(a.G.nodes())

    assert n_nodes_1 > n_nodes_0
