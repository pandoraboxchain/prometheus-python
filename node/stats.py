from chain.merging_iterator import MergingIter
from chain.resolver import Resolver

class Stats:
    @staticmethod
    def gather(node):
        node.logger.info("Gathering stats...")        

        dag = node.dag
        epoch = node.epoch
        total_block_rewards = 0
        payments = []
        for top, _ in epoch.get_epoch_hashes().items():
            iterator = MergingIter(dag, node.conflict_watcher, top)
            for block in iterator:
                if block:
                    if not block.block.payment_txs:
                        continue #it might be genesis, or just some silly validator who decided not to earn a reward
                    block_reward = block.block.payment_txs[0]
                    total_block_rewards += block_reward.amounts[0]
                    payments.append(block.block.payment_txs)
        

        payments = list(reversed(payments))
        _, unspent_list = Resolver.resolve(payments)

        unspent_total = 0
        for unspent in unspent_list:
            unspent_tx = dag.payments_by_hash[unspent.tx]
            unspent_output = unspent.number
            unspent_amount = unspent_tx.amounts[unspent_output]
            unspent_total += unspent_amount

        node.logger.info("Total emitted money %s", total_block_rewards)
        node.logger.info("Unspent money %s", unspent_total)