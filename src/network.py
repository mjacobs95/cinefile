import networkx as nx

from pathlib import Path
from api import DataLoader
from collections import Counter
from pyvis.network import Network


root_dir = Path(__file__).resolve().parent.parent
out_dir = root_dir / 'outputs'


class NetworkBuilder(DataLoader):

    connected = 0
    check_chunk = 500

    egde_color = 'gray'
    edge_font_size = 7

    base_node_color = 'green'
    movie_node_color = 'red'
    actor_node_color = 'blue'
    node_font_size = 10

    def __init__(self, 
                 mode = "movie",
                 string_0 = "jaws",
                 string_1 = "dumb and dumber",
                 actor_lim = 5, # higher this is, the more B-listers
                 movie_lim = 10, # higher this is, fewer iterations required I imagine
                 iter_lim = 4):
        """Initialises the object.

        Args:
            mode (str, optional): The node type of the first two entities. Defaults to "movie".
            string_0 (str, optional): Entity name 1. Defaults to "jaws".
            string_1 (str, optional): Entity name 2. Defaults to "dumb and dumber".
            actor_lim (int, optional): API limit on n actors returned per movie. Defaults to 5.
            movie_lim (int, optional): API limit on n movies returned per actor Defaults to 10.
            iter_lim (int, optional): Limit on the number of iterations to run for before breaking. Defaults to 4. 
        """

        super().__init__(actor_lim = actor_lim, movie_lim = movie_lim)
        self.iter_lim = iter_lim

        self.G = G = nx.Graph()

        # for filename
        self.string_0 = string_0.replace(" ", "")
        self.string_1 = string_1.replace(" ", "")

        # mode
        if mode == "movie":

            subdict_0 = self.search_movie(name = string_0)
            subdict_1 = self.search_movie(name = string_1)

        elif mode == "actor":

            subdict_0 = self.search_actor(name = string_0)
            subdict_1 = self.search_actor(name = string_1)

        self.base_node_0 = self.add_node(subdict_0, node_type = mode, base_node = True)
        self.base_node_1 = self.add_node(subdict_1, node_type = mode, base_node = True)

        self.update_unexpanded_ids()

        return
    

    def generate_node_id(self):
        """Generates unique ID for a new node.

        Returns:
            int: New node ID.
        """

        node_list = list(self.G.nodes)

        if len(node_list) == 0:
            new_id = 0

        else:
            new_id = max(node_list) + 1

        return new_id
    

    def add_node(self, subdict, node_type = 'movie', base_node = False):
        """Adds new node to graph. 

        Args:
            subdict (dict): Entity data from API. 
            node_type (str, optional): Node type. Defaults to 'movie'.
            base_node (bool, optional): Whether the node is one of the first two placed. Defaults to False.

        Returns:
            int: New node ID.
        """

        if base_node:
            color = self.base_node_color
        else:
            if node_type == 'movie':
                color = self.movie_node_color
            elif node_type == 'actor':
                color = self.actor_node_color

        new_id = self.generate_node_id()
        attribute_dict = {**subdict, 'type': node_type, 'expanded':False, 'color':color, 'font':{'size':self.node_font_size}}

        if 'title' in subdict.keys():
            attribute_dict['label'] = subdict.get('title')
        elif 'name' in subdict.keys():
            attribute_dict['label'] = subdict.get('name')

        print("\t\tAdding node {}: {}".format(new_id, attribute_dict['label']))
        self.G.add_nodes_from([(new_id, attribute_dict)])

        return new_id
    

    def update_unexpanded_ids(self):
        """Updates a list of unexpanded nodes.
        """

        nodes = self.G.nodes.data()
        self.nodes_unexpanded = [node for node in nodes if node[1]['expanded'] == False]

        return
    

    def expand_node(self, node_tuple):
        """Adds new nodes for entities associated with an unexpanded node. Draws edges to the new nodes. 

        Args:
            node_tuple (tuple): Tuple containing node ID and TMDB ID. 
        """

        node_id = node_tuple[0]
        api_id = node_tuple[1].get('id')
        node_type = node_tuple[1].get('type')

        if node_type == 'movie':
            data = self.get_movie_credits(movie_id = api_id)
            new_node_type = 'actor'

        elif node_type == 'actor':
            data = self.get_actor_credits(person_id = api_id)
            new_node_type = 'movie'

        for subdict in data:

            character = subdict.get('character')
            del subdict['character']

            new_id = self.add_node(subdict, node_type = new_node_type)
            self.G.add_edge(node_id, new_id, **{'label':character, 'font':{'size':self.edge_font_size}, 'color':self.egde_color})

        return
    

    def get_duplicated_nodes(self):
        """Gets sets of duplicated nodes. 

        Returns:
            dict: Dictionary of duplicated node IDs, indexed by TMBD ID. 
        """

        dup_dict = {}

        for node_type in ['actor', 'movie']:

            new_ids = [{'node_id':node_tuple[0], 'api_id':node_tuple[1]['id']} for node_tuple in self.G.nodes.data() if node_tuple[1].get('type',0) == node_type]
            c = Counter([subdict.get('api_id') for subdict in new_ids])

            dup_list = [api_id for api_id, count in dict(c).items() if count > 1]
            dup_dict[node_type] = {api_id:[subdict.get('node_id') for subdict in new_ids if subdict['api_id'] == api_id] for api_id in dup_list}

        return dup_dict


    def expand_all(self, resolve = True):
        """Expands all unexpanded nodes using self.expand_node(). 

        Args:
            resolve (bool, optional): Whether to resolve duplicate nodes. Defaults to True.
        """

        nodes_unexpanded = self.nodes_unexpanded

        # iterate through unexpanded nodes expanding them
        for node_tuple in nodes_unexpanded:

            if node_tuple[0] % self.check_chunk == 0: # break if connected
                if self.check_if_connected() == 1:
                    break

            print("\tExpanding node {}: {}".format(node_tuple[0], node_tuple[1].get("label")))
            self.expand_node(node_tuple)

        # set expanded to True for previously unexpanded nodes
        attrs = {node_tuple[0]:{'expanded':True} for node_tuple in nodes_unexpanded}
        nx.set_node_attributes(self.G, attrs)

        if resolve:
            self.resolve_nodes()

        # update unexpanded node ids
        self.update_unexpanded_ids()
        
        return
    

    def resolve_nodes(self):
        """Resolve all sets of duplicated nodes. 
        """

        dup_dict = self.get_duplicated_nodes()

        for node_type in ['actor', 'movie']:
            
            subdict = dup_dict.get(node_type)

            if len(subdict.keys()) > 0:

                for api_id, node_id_list in subdict.items():

                    self.merge_node_group(node_id_list)

        return
    

    def merge_node_group(self, node_id_list):
        """Merge a set of duplicate nodes by deleting nodes and editing edges. 

        Args:
            node_id_list (list): List of node IDs that we want to merge. 
        """

        keep_node = node_id_list[0]
        remove_list = node_id_list[1:]

        edge_list = [edge for edge in self.G.edges.data() if edge[0] in remove_list or edge[1] in remove_list]
        
        for edge in edge_list:

            attrs = edge[2]
            edge_tuple = (edge[0], edge[1])

            change_node = list(set(set(edge_tuple) & set(remove_list)))[0]
            change_idx = edge_tuple.index(change_node)
            keep_idx = 0 if change_idx == 1 else 1

            self.G.remove_edge(edge_tuple[0], edge_tuple[1])
            self.G.add_edge(edge_tuple[keep_idx], keep_node, **attrs)

        for node_id in remove_list:
            self.G.remove_node(node_id)

        return
    

    def check_if_connected(self):
        """Checks if the two base nodes are connected.

        Returns:
            int: Whether the graph is connected. Can only take the values 0 or 1. 
        """

        self.connected = nx.node_connectivity(self.G, s=self.base_node_0, t=self.base_node_1)

        if self.connected == 1:
            print("Graph is connected!")

        return self.connected


    def main(self, iter_lim = None):
        """Iteratively invokes self.expand_all() and self.check_if_connected() until graph is connected or iter_lim reached. 

        Args:
            iter_lim (int, optional): Limit on the number of iterations to run for before breaking. Defaults to None.
        """

        iter_lim = self.iter_lim if iter_lim == None else iter_lim

        for iter in range(iter_lim):

            print("On iteration: {}".format(iter + 1))

            self.expand_all(resolve = True)
            connected = self.check_if_connected()

            if connected == 1:

                break

        return
    

    def get_shortest_paths(self):
        """Gets all shortest paths between base nodes if they are connected. 

        Returns:
            list: List of shortest paths. 
        """

        if self.connected:
            p = nx.all_shortest_paths(self.G, source = self.base_node_0, target = self.base_node_1)

        else:
            print("Graph is not connected!")
            p = []

        return p 
    

    def streamline_from_path(self):
        """Induces subgraph of the shortest paths between base nodes. 

        Returns:
            networkx.graph.Graph: Induced subgraph.
        """

        p = self.get_shortest_paths()
        nodes_sub = set([item for sublist in p for item in sublist])
        G_sub = nx.induced_subgraph(self.G, nodes_sub)

        return G_sub


    def plot(self, size = '1000px', streamline = True, filename = None):
        """Plots graph as .html file. 

        Args:
            size (str, optional): Image size. Defaults to '1000px'.
            streamline (bool, optional): Whether to streamline graph to shortest path. Defaults to True.
            filename (str, optional): Desired .html filename. Defaults to None.
        """

        nt = Network(size, size)

        G = self.G

        if streamline:
            G = self.streamline_from_path()
        
        nt.from_nx(G)

        if filename == None:
            filename = "{}_{}.html".format(self.string_0, self.string_1)

        filepath = str(out_dir / filename)
        nt.show(filepath, notebook=False)

        return





if __name__ == '__main__':

    a = NetworkBuilder(mode = "movie",
                       string_0 = "star wars",
                       string_1 = "monsters inc",
                       actor_lim = 5, 
                       movie_lim = 10)

    a.main(iter_lim = 4)

    a.plot(streamline = True, filename = "demo.html")

    
    


