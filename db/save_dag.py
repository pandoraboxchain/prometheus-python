import os

def save_dag(dag, folder):
    p = os.path.join(os.getcwd(), folder, 'dag')
    outfile = open(p, 'w')

    m = max(dag.blocks_by_number.keys())
    blocks = []
    for n in range(0, m+1):
        if n in self.blocks_by_number:
            bs = ",".join([i.get_hash() for i in dag.blocks_by_number[n])
            blocks.append(bs)
        else:
            blocks.append("")
        dag.blocks_by_number.get_hash()
    outfile.write("\n".join(itemlist))
