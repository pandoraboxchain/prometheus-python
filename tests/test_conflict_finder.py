import unittest

from chain.confirmation_requirement import ConfirmationRequirement
from chain.dag import Dag
from crypto.private import Private
from tests.test_chain_generator import TestChainGenerator
from visualization.dag_visualizer import DagVisualizer
from chain.conflict_finder import ConflictFinder


class TestConflictFinder(unittest.TestCase):

    def test_find_conflicts_longest_chain(self):
        dag = Dag(0)
        # generate test case
        # time_slot [0, 1, 2, 3, 4, 5, 6]
        # -------------------------------
        # 1 ------- [0, 1, 2, 3, 4, 5, 6]
        # 2 ------- [ ,  ,  , 3, 4, 5,  ]
        # 3 ------- [ ,  ,  ,  , 4, 5,  ]
        # block number 3 MUST BE signed by same key
        private1 = Private.generate()
        private2 = Private.generate()
        private3 = Private.generate()

        determinated_top_hash = \
        TestChainGenerator.fill_with_dummies_and_skips(dag=dag,
                                                       prev_hash=dag.genesis_block().get_hash(),
                                                       range=range(1, 7),
                                                       indices_to_skip=[],
                                                       dummy_private=private1)

        TestChainGenerator.fill_with_dummies_and_skips(dag=dag,
                                                       prev_hash=dag.blocks_by_number[2][0].get_hash(),
                                                       range=range(3, 6),
                                                       indices_to_skip=[],
                                                       dummy_private=private2)

        TestChainGenerator.fill_with_dummies_and_skips(dag=dag,
                                                       prev_hash=dag.blocks_by_number[3][1].get_hash(),
                                                       range=range(4, 6),
                                                       indices_to_skip=[],
                                                       dummy_private=private3)

        # DagVisualizer.visualize(dag)

        conflict_finder = ConflictFinder(dag)
        top_blocks = list(dag.get_top_blocks().keys())
        top, conflicts = conflict_finder.find_conflicts(top_blocks)
        # assert determined top
        self.assertEqual(determinated_top_hash, top)
        # test conflicts [3],[4,4],[5,5] EXCLUDE flatten top chain from list of conflict block hashes
        self.assertEqual(len(conflicts), 5)

    def test_find_conflicts_random_chain(self):
        dag = Dag(0)
        # generate test case
        # time_slot [0, 1, 2, 3, 4, 5]
        # -------------------------------
        # 1 ------- [0, 1, 2, 3, 4, 5]
        # 2 ------- [ ,  ,  , 3, 4, 5]
        # 3 ------- [ ,  ,  ,  , 4, 5]
        # block number 3 MUST BE signed by same key
        private1 = Private.generate()
        private2 = Private.generate()
        private3 = Private.generate()

        top_hash_1 = \
            TestChainGenerator.fill_with_dummies_and_skips(dag=dag,
                                                           prev_hash=dag.genesis_block().get_hash(),
                                                           range=range(1, 6),
                                                           indices_to_skip=[],
                                                           dummy_private=private1)
        top_hash_2 = \
            TestChainGenerator.fill_with_dummies_and_skips(dag=dag,
                                                           prev_hash=dag.blocks_by_number[2][0].get_hash(),
                                                           range=range(3, 6),
                                                           indices_to_skip=[],
                                                           dummy_private=private2)

        top_hash_3 = \
            TestChainGenerator.fill_with_dummies_and_skips(dag=dag,
                                                           prev_hash=dag.blocks_by_number[3][1].get_hash(),
                                                           range=range(4, 6),
                                                           indices_to_skip=[],
                                                           dummy_private=private3)

        # DagVisualizer.visualize(dag)

        conflict_finder = ConflictFinder(dag)
        top_blocks = list(dag.get_top_blocks().keys())
        top, conflicts = conflict_finder.find_conflicts(top_blocks)
        # assert determined top (it can be one of top_hash1,2,3)
        tops = [top_hash_1, top_hash_2, top_hash_3]
        self.assertIn(top, tops)
        # test conflicts
        # conflicts include all [3],[4,4],[5,5] EXCLUDE flatten top chain from list of conflict block hashes
        self.assertEqual(len(conflicts), 5)

    def test_conflicts_with_skips(self):
        dag = Dag(0)
        # generate test case
        # time_slot [0, 1, 2, 3, 4, 5]
        # -------------------------------
        # 1 ------- [0, 1, 2, 3,  , 5, 6, 7, 8]
        # 2 ------- [ ,  ,  , 3, 4,  , 6, 7, 8]
        # 3 ------- [ ,  ,  ,  , 4, 5, 6,  , 8]
        # block number 3 MUST BE signed by same key
        private1 = Private.generate()
        private2 = Private.generate()
        private3 = Private.generate()

        top_hash_1 = \
            TestChainGenerator.fill_with_dummies_and_skips(dag=dag,
                                                           prev_hash=dag.genesis_block().get_hash(),
                                                           range=range(1, 9),
                                                           indices_to_skip=[4],
                                                           dummy_private=private1)
        top_hash_2 = \
            TestChainGenerator.fill_with_dummies_and_skips(dag=dag,
                                                           prev_hash=dag.blocks_by_number[2][0].get_hash(),
                                                           range=range(3, 9),
                                                           indices_to_skip=[5],
                                                           dummy_private=private2)

        top_hash_3 = \
            TestChainGenerator.fill_with_dummies_and_skips(dag=dag,
                                                           prev_hash=dag.blocks_by_number[3][1].get_hash(),
                                                           range=range(4, 9),
                                                           indices_to_skip=[7],
                                                           dummy_private=private3)

        # DagVisualizer.visualize(dag)

        conflict_finder = ConflictFinder(dag)
        top_blocks = list(dag.get_top_blocks().keys())
        top, conflicts = conflict_finder.find_conflicts(top_blocks)
        # assert determined top (it can be one of top_hash1,2,3)
        tops = [top_hash_1, top_hash_2, top_hash_3]
        self.assertIn(top, tops)
        if top == top_hash_1:
            # test conflicts
            # conflicts include all [3],[4,4],[5],[6,6],[7],[8,8]
            # EXCLUDE flatten top chain from list of conflict block hashes
            self.assertEqual(len(conflicts), 9)
        if top == top_hash_2:
            # test conflicts
            # conflicts include all [3],[4],[5,5],[6,6],[7],[8,8]
            # EXCLUDE flatten top chain from list of conflict block hashes
            self.assertEqual(len(conflicts), 9)
        if top == top_hash_3:
            # test conflicts
            # conflicts include all [3],[4],[5],[6,6],[7,7],[8,8]
            # EXCLUDE flatten top chain from list of conflict block hashes
            self.assertEqual(len(conflicts), 9)

    def test_complicated_dag_with_skips(self):
        dag = Dag(0)
        # generate test case
        # time_slot [0, 1, 2, 3, 4, 5]
        # -------------------------------
        # 1 ------- [-, -, 2, 3, 4, 5,  ,  , 8]
        # 2 ------- [0, 1, 2,  ,  , 5, 6, 7, 8]
        # 3 ------- [-, -, -, 3, 4,  , 6, 7, 8]
        # 4 ------- [-, -, -, -, 4, 5, 6,  , 8]
        # block number 3 MUST BE signed by same key
        private1 = Private.generate()
        private2 = Private.generate()
        private3 = Private.generate()
        private4 = Private.generate()

        top_hash_2 = \
            TestChainGenerator.fill_with_dummies_and_skips(dag=dag,
                                                           prev_hash=dag.genesis_block().get_hash(),
                                                           range=range(1, 9),
                                                           indices_to_skip=[3, 4],
                                                           dummy_private=private2)

        top_hash_1 = \
            TestChainGenerator.fill_with_dummies_and_skips(dag=dag,
                                                           prev_hash=dag.blocks_by_number[1][0].get_hash(),
                                                           range=range(2, 9),
                                                           indices_to_skip=[6, 7],
                                                           dummy_private=private1)

        top_hash_3 = \
            TestChainGenerator.fill_with_dummies_and_skips(dag=dag,
                                                           prev_hash=dag.blocks_by_number[2][0].get_hash(),
                                                           range=range(3, 9),
                                                           indices_to_skip=[5],
                                                           dummy_private=private3)

        top_hash_4 = \
            TestChainGenerator.fill_with_dummies_and_skips(dag=dag,
                                                           prev_hash=dag.blocks_by_number[3][1].get_hash(),
                                                           range=range(4, 9),
                                                           indices_to_skip=[7],
                                                           dummy_private=private4)

        # DagVisualizer.visualize(dag)

        conflict_finder = ConflictFinder(dag)
        top_blocks = list(dag.get_top_blocks().keys())
        top, conflicts = conflict_finder.find_conflicts(top_blocks)
        # assert determined top (it can be one of longest top_hash_3,4)
        tops = [top_hash_3, top_hash_4]
        self.assertIn(top, tops)
        # test conflicts
        self.assertEqual(len(conflicts), 13)

    def test_complicated_dag_with_skips_and_determined_top(self):
        dag = Dag(0)
        # generate test case
        # time_slot [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        # ----------------------------------------
        # 1 ------- [ ,  , 2, 3, 4,  ,  ,  , 8,  ]
        # 2 ------- [0, 1, 2,  ,  , 5, 6, 7, 8, 9]
        # 3 ------- [ ,  ,  , 3, 4,  , 6, 7, 8,  ]
        # 4 ------- [ ,  ,  ,  , 4, 5, 6,  , 8,  ]
        # 5 ------- [ ,  , 2, 3,  ,  ,  ,  ,  , 9]
        # block number 3 MUST BE signed by same key
        private1 = Private.generate()
        private2 = Private.generate()
        private3 = Private.generate()
        private4 = Private.generate()
        private5 = Private.generate()

        top_hash_2 = \
            TestChainGenerator.fill_with_dummies_and_skips(dag=dag,
                                                           prev_hash=dag.genesis_block().get_hash(),
                                                           range=range(1, 11),
                                                           indices_to_skip=[3, 4, 10],
                                                           dummy_private=private2)

        top_hash_1 = \
            TestChainGenerator.fill_with_dummies_and_skips(dag=dag,
                                                           prev_hash=dag.blocks_by_number[1][0].get_hash(),
                                                           range=range(2, 11),
                                                           indices_to_skip=[6, 7],
                                                           dummy_private=private1)

        top_hash_3 = \
            TestChainGenerator.fill_with_dummies_and_skips(dag=dag,
                                                           prev_hash=dag.blocks_by_number[2][0].get_hash(),
                                                           range=range(3, 11),
                                                           indices_to_skip=[5, 7, 10],
                                                           dummy_private=private3)

        top_hash_4 = \
            TestChainGenerator.fill_with_dummies_and_skips(dag=dag,
                                                           prev_hash=dag.blocks_by_number[3][1].get_hash(),
                                                           range=range(4, 11),
                                                           indices_to_skip=[5, 8, 10],
                                                           dummy_private=private4)

        top_hash_5 = \
            TestChainGenerator.fill_with_dummies_and_skips(dag=dag,
                                                           prev_hash=dag.blocks_by_number[3][1].get_hash(),
                                                           range=range(4, 11),
                                                           indices_to_skip=[4, 5, 6, 7, 8],
                                                           dummy_private=private5)

        # DagVisualizer.visualize(dag)

        conflict_finder = ConflictFinder(dag)
        top_blocks = list(dag.get_top_blocks().keys())
        top, conflicts = conflict_finder.find_conflicts(top_blocks)
        self.assertEqual(top, top_hash_1)  # strong determined top (longest chain in current case) min. skipped blocks
        # conflicts include all [2],[3],[4,4],[5],[6,6,6],[7,7],[8,8],[9,9,9,9],[10]
        # EXCLUDE flatten top chain from list of conflict block hashes
        self.assertEqual(len(conflicts), 17)

    def test_merged_dag(self):
        dag = Dag(0)
        # generate test case
        # time_slot [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        # ----------------------------------------
        # 1 ------- [0, 1, 2, 3, 4]
        # 2 ------- [-, -, 2, s, s]
        # 3 ------- [-, -, 2, s, s]
        # 4 ------- [-, -, 2, 3, s]
        # s - same block (merged)
        conf_req = ConfirmationRequirement(dag)

        genesis_hash = dag.genesis_block().get_hash()

        block_hash = TestChainGenerator.insert_dummy(dag, [genesis_hash], 1)
        conf_req.blocks[block_hash] = 2
        block_hash = TestChainGenerator.insert_dummy(dag, [genesis_hash], 1)
        conf_req.blocks[block_hash] = 3
        block_hash = TestChainGenerator.insert_dummy(dag, dag.get_top_hashes(), 2)
        conf_req.blocks[block_hash] = 3
        last_block_in_seq_hash = TestChainGenerator.insert_dummy(dag, [genesis_hash], 1)
        conf_req.blocks[last_block_in_seq_hash] = 3
        block_hash = TestChainGenerator.insert_dummy(dag, [genesis_hash], 1)
        conf_req.blocks[block_hash] = 3
        block_hash = TestChainGenerator.insert_dummy(dag, [last_block_in_seq_hash, block_hash], 2)
        conf_req.blocks[block_hash] = 4
        block_hash = TestChainGenerator.insert_dummy(dag, dag.get_top_hashes(), 3)
        conf_req.blocks[block_hash] = 4
        top_hash = TestChainGenerator.insert_dummy(dag, dag.get_top_hashes(), 4)

        # DagVisualizer.visualize(dag)

        conflict_finder = ConflictFinder(dag)
        top_blocks = list(dag.get_top_blocks().keys())
        top, conflicts = conflict_finder.find_conflicts(top_blocks)
        self.assertEqual(top, top_hash)  # strong determined top
        # CHAIN ALREADY MERGED
        self.assertEqual(len(conflicts), 0)

