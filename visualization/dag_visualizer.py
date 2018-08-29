from graphviz import Digraph

class DagVisualizer:
    @staticmethod
    def visualize(dag):
        dot = Digraph(name='DAG', node_attr={
            'shape':'box',\
            'style': "rounded"})
        dot.attr(rankdir = 'RL')
        links = []

        max_block_number = max(dag.blocks_by_number.keys())
        for number in range(max_block_number+1):
            block_list_by_number = dag.blocks_by_number.get(number, [])
    
            with dot.subgraph() as sub:
                sub.attr(rank = 'same')
                
                #place number
                sub.node(str(number), shape="plain")
                if number != 0: 
                    dot.edge(str(number), str(number-1), style="invis")
                
                #add blocks on this level if any
                for block in block_list_by_number:
                    links += block.block.prev_hashes
                    blockhash = block.get_hash()
                    color = 'black'
                    if blockhash == dag.genesis_block().get_hash():
                        color='blue'
                    sub.node(blockhash.hex()[0:6], color=color)

        for _, signed_block in dag.blocks_by_hash.items():
            block_hash = signed_block.get_hash()
            for prev_hash in signed_block.block.prev_hashes:
                dot.edge(block_hash.hex()[0:6], prev_hash.hex()[0:6], constraint='true')
        #set view to True to instantly render and open pdf
        #Note, that you will need 'graphviz' package installed
        dot.render('visualization/dag.dot', view=False) 
