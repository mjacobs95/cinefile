import networkx as nx
import dash_daq as daq
import dash_cytoscape as cyto

#from network import NetworkBuilder
from api import DataLoader
from collections import Counter
from itertools import combinations
from dash import Dash, html, Input, Output, State, callback, dcc

edges = []
nodes = []

default_stylesheet = [
        {
            'selector': 'node',
            'style': {
                'label': 'data(label)'
            }
        },
        {
            'selector': '[type = "movie"]',
            'style': {
                'background-color': 'red',
                'shape': 'circle'
            }
        },
        {
            'selector': '[type = "actor"]',
            'style': {
                'background-color': 'blue',
                'shape': 'circle'
            }
        },
        {
            'selector': 'edge',
            'style': {'content': 'data(label)',
                    'curve-style': 'straight',
                    'width': 1,
                    'line-color': 'lightblue',
                    'text-margin-x': 0,
                    'font-size': 8}
        }
    ]



class NetworkApp(DataLoader):

    def __init__(self, 
                 actor_lim = 3, 
                 movie_lim = 3):
        
        self.connected = False
        self.base_nodes = []

        super().__init__(actor_lim = actor_lim, movie_lim = movie_lim)

        self.app = Dash(__name__)

        self.G = nx.Graph()
        self.actor_lim = actor_lim
        self.movie_lim = movie_lim

        self.app.layout = html.Div([
            html.Div([
                dcc.Input(
                            id="node_name",
                            type="text",
                            placeholder="enter name",
                        ),
                dcc.RadioItems(
                    options={
                            'movie': 'movie',
                            'actor': 'actor'
                    },
                    value='movie', 
                    id = 'mode',
                    labelStyle={'display': 'inline-block'}
                        )]),
            html.Div([
                html.Button('add node', id='btn_add_node', n_clicks_timestamp=0),
                html.Button('expand nodes', id='btn_expand', n_clicks_timestamp=0),
                html.Button('streamline', id='btn_streamline', n_clicks_timestamp=0),
                html.Button('reset', id='btn_reset', n_clicks_timestamp=0)
            ]),
            html.Div([
                daq.NumericInput(id='movie_lim',
                                 label='movie lim',
                                 labelPosition='bottom',
                                 style={'display': 'inline-block'},
                                 value=movie_lim),
                daq.NumericInput(id='actor_lim',
                                 label='actor lim',
                                 labelPosition='bottom',
                                 style={'display': 'inline-block'},
                                 value=actor_lim)
            ], style={'display': 'inline-block'}),
            html.Br(),
            html.Div(id='connected_bool'),

            cyto.Cytoscape(
                id='cytoscape-elements-callbacks',
                layout={'name': 'circle'},
                style={'width': '100%', 'height': '450px'},
                elements=edges+nodes,
                stylesheet=default_stylesheet
            )
        ])

        # base nodes
        self.app.callback(
            Output('cytoscape-elements-callbacks', 'elements', allow_duplicate=True),
            Input('btn_add_node', 'n_clicks'),
            State('node_name', 'value'),
            State('mode', 'value'),
            prevent_initial_call=True)(self.add_base_node)
        
        # expand nodes
        self.app.callback(
            Output('cytoscape-elements-callbacks', 'elements', allow_duplicate=True),
            State('movie_lim', 'value'),
            State('actor_lim', 'value'),
            Input('btn_expand', 'n_clicks'),
            prevent_initial_call=True)(self.expand_all)
        
        # streamline
        self.app.callback(
            Output('cytoscape-elements-callbacks', 'elements', allow_duplicate=True),
            Input('btn_streamline', 'n_clicks'),
            prevent_initial_call=True)(self.streamline_from_path)
        
        # reset
        self.app.callback(
            Output('cytoscape-elements-callbacks', 'elements', allow_duplicate=True),
            Input('btn_reset', 'n_clicks'),
            prevent_initial_call=True)(self.reset)
        
        
        return
        
    
    def reset(self, btn_reset):

        self.__init__()
        #self.G.clear()

        print("resetting")

        return []+[]


    def add_base_node(self, n_clicks, name_string, mode):

        if mode == "movie":

            subdict = self.search_movie(name = name_string)

        elif mode == "actor":

            subdict = self.search_actor(name = name_string)

        if len(self.G.nodes) == 0:

            self.base_nodes.append(self.add_node(subdict, node_type = mode))

        elif len(self.G.nodes) == 1 and not self.connected:

            self.base_nodes.append(self.add_node(subdict, node_type = mode))

        elif len(self.G.nodes) > 1 and self.connected:

            self.base_nodes.append(self.add_node(subdict, node_type = mode))
            self.connected = False

        else:
            print("Too many unconnected nodes!") # replace this later with a count of number of nodes

        self.update_unexpanded_ids()
        elements = self.graph_to_elements()

        return elements


    def add_node(self, subdict, node_type = 'movie'):
        """Adds new node to graph. 

        Args:
            subdict (dict): Entity data from API. 
            node_type (str, optional): Node type. Defaults to 'movie'.

        Returns:
            int: New node ID.
        """

        new_id = self.generate_node_id()
        attribute_dict = {**subdict, 'type': node_type, 'expanded':False}#, 'color':color, 'font':{'size':self.node_font_size}}

        if 'title' in subdict.keys():
            attribute_dict['label'] = subdict.get('title')
        elif 'name' in subdict.keys():
            attribute_dict['label'] = subdict.get('name')

        #self.log.info("\t\tAdding node {}: {}".format(new_id, attribute_dict['label']))
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
            self.G.add_edge(node_id, new_id, **{'label':character})#, 'font':{'size':self.edge_font_size}, 'color':self.egde_color})

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


    def expand_all(self, movie_lim, actor_lim, n_clicks, resolve = True):
        """Expands all unexpanded nodes using self.expand_node(). 

        Args:
            resolve (bool, optional): Whether to resolve duplicate nodes. Defaults to True.
        """

        if movie_lim != self.movie_lim:
            self.movie_lim = movie_lim

        if actor_lim != self.actor_lim:
            self.actor_lim = actor_lim

        nodes_unexpanded = self.nodes_unexpanded

        # iterate through unexpanded nodes expanding them
        for node_tuple in nodes_unexpanded:

            # if node_tuple[0] % self.check_chunk == 0: # break if connected
            #     if self.check_if_connected() == 1:
            #         break

            #self.log.info("\tExpanding node {}: {}".format(node_tuple[0], node_tuple[1].get("label")))
            self.expand_node(node_tuple)

        # set expanded to True for previously unexpanded nodes
        attrs = {node_tuple[0]:{'expanded':True} for node_tuple in nodes_unexpanded}
        nx.set_node_attributes(self.G, attrs)

        if resolve:
            self.resolve_nodes()

        # update unexpanded node ids
        self.update_unexpanded_ids()

        self.check_if_connected()

        elements = self.graph_to_elements()
        
        return elements
    

    def check_if_connected(self):
        """Checks if the two base nodes are connected.

        Returns:
            int: Whether the graph is connected. Can only take the values 0 or 1. 
        """

        print("base nodes: ", self.base_nodes)
        print("all nodes: ", self.G.nodes)


        self.connected = all([nx.node_connectivity(self.G, pair[0], pair[1]) for pair in combinations(self.base_nodes, 2)]) # all pairs of base nodes connected
        #self.connected = nx.node_connectivity(self.G, s=self.base_nodes[0], t=self.base_nodes[1])

        if self.connected:
            print("Graph is connected!")

        return self.connected
    

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
    

    def update_unexpanded_ids(self):
        """Updates a list of unexpanded nodes.
        """

        nodes = self.G.nodes.data()
        self.nodes_unexpanded = [node for node in nodes if node[1]['expanded'] == False]

        return
    
    def get_shortest_paths(self):
        """Gets all shortest paths between base nodes if they are connected. 

        Returns:
            list: List of shortest paths. 
        """

        p = []

        if self.connected:
        
            for pair in combinations(self.base_nodes, 2):
                p.append(nx.all_shortest_paths(self.G, source = pair[0], target = pair[1]))
            
        else:
            print("Graph is not connected!")
            return

        paths = [item for sublist in p for item in sublist]

        return paths
    

    def streamline_from_path(self, n_clicks):
        """Induces subgraph of the shortest paths between base nodes. 

        Returns:
            networkx.graph.Graph: Induced subgraph.
        """

        paths = self.get_shortest_paths()
        nodes_sub = set([item for sublist in paths for item in sublist])
        self.G = nx.induced_subgraph(self.G, nodes_sub)

        elements = self.graph_to_elements()

        return elements
    
    
    def graph_to_elements(self):

        result = nx.cytoscape_data(self.G)

        nodes = [node_converter(node_dict) for node_dict in result["elements"]["nodes"]]
        edges = [edge_converter(edge_dict) for edge_dict in result["elements"]["edges"]]

        return edges+nodes
    


def node_converter(node_dict):

    node_dict['data'] = {k:str(v) for k,v in node_dict['data'].items()}
    node_dict['data']['id'] = node_dict['data']['value']

    return node_dict

def edge_converter(edge_dict):

    edge_dict['data'] = {k:str(v) for k,v in edge_dict['data'].items()}

    return edge_dict


if __name__ == '__main__':

    a = NetworkApp()

    a.app.run(debug=True)
