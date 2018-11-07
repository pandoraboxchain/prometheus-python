import asyncio

from chain.dag import Dag
from chain.epoch import Epoch


# independent node-like object with sole task to make announcements about start of new rounds and epochs
class AnnouncerNode:
    
    def __init__(self, genesis_creation_time, logger):
        self.logger = logger
        self.dag = Dag(genesis_creation_time)
        self.epoch = Epoch(self.dag)
        self.epoch.set_logger(self.logger)
        self.logger.info("Starting announcer node")
        self.last_announced_round = None
        self.terminated = False

    def step(self):
        current_block_number = self.epoch.get_current_timeframe_block_number()
        if self.epoch.is_new_epoch_upcoming(current_block_number):
            self.logger.info("New epoch upcoming!")

        current_round = self.epoch.get_round_by_block_number(current_block_number)
        if current_round != self.last_announced_round:
            self.logger.info("Starting %s", str(current_round))
            self.last_announced_round = current_round

    async def run(self):
        while True:
            self.step()            
            await asyncio.sleep(1)