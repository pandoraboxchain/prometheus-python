from graphviz import Digraph

class DagVisualizer:
    @staticmethod
    def visualize(dag):
        dot = Digraph(name='DAG', node_attr={
            'shape':'box',\
            'style': "rounded"})
        dot.attr(rankdir = 'RL')
        links = []

        for number, block_list_by_number in dag.blocks_by_number.items():
            if not block_list_by_number:
                    dot.node("skipped" + str(number), style="dotted")
                    continue

            with dot.subgraph() as sub:
                sub.attr(rank = 'same')
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
