from graphviz import Digraph
from chain.conflict_watcher import ConflictWatcher

# Usage
# Just add two following lines where you want to visualize
# And pass dag as argument
# Last argument set to True will try to immediately render and show PDF
# But you have to have graphviz installed in order for this to work
# Please do not commit visualizations since it overwrites file every time it's used

# from visualization.dag_visualizer import DagVisualizer
# DagVisualizer.visualize(dag, True)

# To highlight conflicts you can do the following:
# visualizer = DagVisualizer(dag, conflict_watcher)
# visualizer.show()

class DagVisualizer:
    def __init__(self, dag, conflict_watcher=None):
        self.dag = dag
        self.watcher = conflict_watcher
        self.reset_colors()

    def show(self):
        self.render(name="dag", view_immediately=True)

    def render(self, name="dag", view_immediately=False):
        dot = Digraph(name='DAG', node_attr={
            'shape':'box',\
            'style': "rounded"})
        dot.attr(rankdir = 'RL')
        links = []

        max_block_number = max(self.dag.blocks_by_number.keys())
        for number in range(max_block_number+1):
            block_list_by_number = self.dag.blocks_by_number.get(number, [])
    
            with dot.subgraph() as sub:
                sub.attr(rank = 'same')
                
                #place number
                sub.node(str(number), shape="plain")
                if number != 0: 
                    dot.edge(str(number), str(number-1), style="invis")
                
                blocks_to_color = {}

                #add blocks on this level if any
                for block in block_list_by_number:
                    links += block.block.prev_hashes
                    block_hash = block.get_hash()
                    color = self.get_block_color(block_hash)
                    sub.node(block_hash.hex()[0:6], color=color)

        for _, signed_block in self.dag.blocks_by_hash.items():
            block_hash = signed_block.get_hash()
            for prev_hash in signed_block.block.prev_hashes:
                dot.edge(block_hash.hex()[0:6], prev_hash.hex()[0:6], constraint='true')
        
        self.reset_colors()
        #set view to True to instantly render and open pdf
        #Note, that you will need 'graphviz' package installed
        dot.format = "png"
        dot.render('visualization/' + name + '.dot', view=view_immediately) 

    def reset_colors(self):
        self.possible_conflict_colors = ["red", "orangered", "firebrick", "orange", "brown"]
        self.blocks_color = {}

    # to show conflicting blocks in the same color
    def get_block_color(self, block_hash):
        if not self.watcher:
            return "black"

        if block_hash in self.blocks_color:
            return self.blocks_color[block_hash]
        
        conflicts = self.watcher.get_conflicts_by_block(block_hash)
        if conflicts:
            chosen_color = self.possible_conflict_colors.pop()
            for conflict in conflicts:
                self.blocks_color[conflict] = chosen_color
            return chosen_color

        return "black"

    @staticmethod
    def visualize(dag, view_immediately=False):
        visualizer = DagVisualizer(dag)
        visualizer.render("dag", view_immediately)
