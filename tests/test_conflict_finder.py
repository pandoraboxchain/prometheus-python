import unittest

from chain.dag import Dag
from crypto.private import Private
from tests.test_chain_generator import TestChainGenerator
from visualization.dag_visualizer import DagVisualizer
from chain.conflict_finder import ConflictFinder


class TestConflictFinder(unittest.TestCase):

    #@unittest.skip('update tests')
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
                                                       range=range(1, 7, 1),
                                                       indices_to_skip=[],
                                                       dummy_private=private1)

        TestChainGenerator.fill_with_dummies_and_skips(dag=dag,
                                                       prev_hash=dag.blocks_by_number[2][0].get_hash(),
                                                       range=range(3, 6, 1),
                                                       indices_to_skip=[],
                                                       dummy_private=private2)

        TestChainGenerator.fill_with_dummies_and_skips(dag=dag,
                                                       prev_hash=dag.blocks_by_number[3][1].get_hash(),
                                                       range=range(4, 6, 1),
                                                       indices_to_skip=[],
                                                       dummy_private=private3)

        DagVisualizer.visualize(dag)

        conflict_finder = ConflictFinder(dag)
        top_blocks = list(dag.get_top_blocks().keys())
        top, conflicts = conflict_finder.find_conflicts(top_blocks)
        # assert determined top
        self.assertEqual(determinated_top_hash, top)
        # test conflicts
        self.assertEqual(len(conflicts), 8)

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
                                                           range=range(1, 6, 1),
                                                           indices_to_skip=[],
                                                           dummy_private=private1)
        top_hash_2 = \
            TestChainGenerator.fill_with_dummies_and_skips(dag=dag,
                                                           prev_hash=dag.blocks_by_number[2][0].get_hash(),
                                                           range=range(3, 6, 1),
                                                           indices_to_skip=[],
                                                           dummy_private=private2)

        top_hash_3 = \
            TestChainGenerator.fill_with_dummies_and_skips(dag=dag,
                                                           prev_hash=dag.blocks_by_number[3][1].get_hash(),
                                                           range=range(4, 6, 1),
                                                           indices_to_skip=[],
                                                           dummy_private=private3)

        DagVisualizer.visualize(dag)
        conflict_finder = ConflictFinder(dag)
        top_blocks = list(dag.get_top_blocks().keys())
        top, conflicts = conflict_finder.find_conflicts(top_blocks)
        # assert determined top (it can be one of top_hash1,2,3)
        tops = [top_hash_1, top_hash_2, top_hash_3]
        self.assertIn(top, tops)
        # test conflicts
        # conflicts include all [3,3],[4,4,4],[5,5] excluding!!! determined top
        self.assertEqual(len(conflicts), 7)

