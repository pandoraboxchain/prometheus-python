from node import Node
from datetime import datetime
import time

class Initializer():  
    
    def __init__(self):
        genesis_creation_time = datetime.datetime.now().time()

        node = Node(genesis_creation_time)
        