from chain.node import Node
import datetime
import time

class Initializer():  
    
    def __init__(self):
        genesis_creation_time = int(datetime.datetime.now().timestamp())
        print("genesis_creation_time", genesis_creation_time)

        node = Node(genesis_creation_time)
        node.run()


        
Initializer()