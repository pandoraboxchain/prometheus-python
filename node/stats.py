from chain.merging_iterator import MergingIter
from chain.resolver import Resolver

class Stats:
    @staticmethod
    def gather(node):
        node.logger.info("Gathering stats...")        

        dag = node.dag
        epoch = node.epoch
        mainchain_block_rewards = 0
        total_block_rewards = 0 #including conflicts
        
        payments = []
        for top, _ in epoch.get_epoch_hashes().items():
            iterator = MergingIter(dag, node.conflict_watcher, top)
            for block in iterator:
                if block:
                    mainchain_block_rewards += Stats.get_block_reward(block.block)
                    payments.append(block.block.payment_txs)

        for blocks_list in dag.blocks_by_number.values():
            for block in blocks_list:
                total_block_rewards += Stats.get_block_reward(block.block)

        payments = list(reversed(payments))
        _, unspent_list = Resolver.resolve(payments)

        unspent_total = 0
        for unspent in unspent_list:
            unspent_tx = dag.payments_by_hash[unspent.tx]
            unspent_output = unspent.number
            unspent_amount = unspent_tx.amounts[unspent_output]
            unspent_total += unspent_amount

        utxo_total = 0
        for tx in node.utxo.utxo.values():
            for output_amount in tx.values():
                utxo_total += output_amount

        node.logger.info("Mainchain emitted funds: %s", mainchain_block_rewards)
        node.logger.info("Unspent funds: %s", unspent_total)
        node.logger.info("Total emitted funds (incl conflicts): %s", total_block_rewards)
        node.logger.info("Utxo confirmed amount: %s", utxo_total)

    @staticmethod #helper method
    def get_block_reward(block):
        if not block.payment_txs:
            return 0 #it might be genesis, or just some silly validator who decided not to earn a reward
        block_reward = block.payment_txs[0]
        return block_reward.amounts[0]