import asyncio
import logging

from chain.dag import Dag
from chain.epoch import Epoch
from chain.params import Round

#independent Node-like object which sole task is to announce different  
class AnnouncerNode():
    
    def __init__(self, genesis_creation_time, logger):
        self.logger = logger
        self.dag = Dag(genesis_creation_time)
        self.epoch = Epoch(self.dag)
        self.epoch.set_logger(self.logger)
        self.dag.subscribe_to_new_block_notification(self.epoch)
        self.logger.info("Starting announcer node")
        self.last_announced_round = None

    async def run(self):
        while True:
            current_block_number = self.epoch.get_current_timeframe_block_number()
            if self.epoch.is_new_epoch_upcoming(current_block_number):
                self.logger.info("New epoch upcoming!")

            current_round = self.epoch.get_round_by_block_number(current_block_number)
            if current_round != self.last_announced_round:
                self.logger.info("Starting %s", str(current_round))
                self.last_announced_round = current_round
                              
            await asyncio.sleep(1)