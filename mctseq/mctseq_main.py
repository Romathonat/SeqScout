# -*- coding: utf-8 -*-

"""Main module."""
import datetime
import copy
import random
import math

from mctseq.utils import read_data, extract_items, uct, \
    count_target_class_data, sequence_mutable_to_immutable, print_results_mcts, \
    subsequence_indices, sequence_immutable_to_mutable
from mctseq.sequencenode import SequenceNode
from mctseq.priorityset import PrioritySetQuality


# TODO: filter redondant elements (post process)
# TODO: Normalize Wracc !!!

# TODO: use bit set to keep extend -> see SPADE too know how to make a temporal join,
# and optimize a lot
# TODO: optimize is_subsequence (not necessary if we do the previous step)

# TODO: implement misere with Wracc
# TODO: better rollout strategies

### LATER
# TODO: Suplementary material notebook
# TODO: Visualisation graph


# IDEA: instead of beginning with the null sequence, take the sequence of max
# length, and enumerate its subsequences (future paper ?)

class MCTSeq():
    def __init__(self, pattern_number, items, data, time_budget, target_class,
                 enable_i=True):
        self.pattern_number = pattern_number
        self.items = items
        self.time_budget = datetime.timedelta(seconds=time_budget)
        self.data = data
        self.target_class = target_class
        self.target_class_data_count = count_target_class_data(data,
                                                               target_class)
        self.enable_i = enable_i
        self.sorted_patterns = PrioritySetQuality()

        # contains sequence-SequenceNode for permutation-unification
        self.root_node = SequenceNode([], None, self.items, self.data,
                                      self.target_class,
                                      self.target_class_data_count,
                                      self.enable_i)

        self.node_hashmap = {}

    def launch(self):
        """
        Launch the algorithm, specifying how many patterns we want to mine
        :return:
        """
        begin = datetime.datetime.utcnow()

        self.node_hashmap[self.root_node.sequence] = self.root_node

        current_node = self.root_node

        iteration_count = 0
        while datetime.datetime.utcnow() - begin < self.time_budget:
            node_sel = self.select(current_node)

            if node_sel != None:
                node_expand = self.expand(node_sel)
                reward = self.roll_out(node_expand)
                self.update(node_expand, reward)
            else:
                # we enter here if we have a terminal node/dead_end. In that case, there
                # is no rollout: the reward is directly the quality of the node
                # self.update(current_node, current_node.quality)
                break
            iteration_count += 1

        print('Nomber iteration: {}'.format(iteration_count))
        # Now we need to explore the tree to get interesting subgroups
        # We use a priority queue to store elements, sorted by their quality

        self.explore_children(self.root_node, self.sorted_patterns)

        return self.sorted_patterns.get_top_k(self.pattern_number)

    def select(self, node):
        """
        Select the best node, using exploration-exploitation tradeoff
        :param node: the node from where we begin to search
        :return: the selected node, or None if exploration is finished
        """
        while not node.is_terminal:
            if not node.is_fully_expanded:
                return node
            else:
                node = self.best_child(node)

                # In that case, it means we reached a dead_end
                if node is None:
                    return None

        # if we reach this point, it means we reached a terminal node
        return None

    def expand(self, node):
        """
        Choose a child to expand among possible children of node
        :param node: the node from wich we want to expand
        :return: the expanded node
        """
        return node.expand(self.node_hashmap)

    def roll_out(self, node):
        """
        Use the same idea as Misere (see paper)
        :param node: the node from wich launch the roll_out
        :return: the quality measure, depending on the reward agregation policy
        """
        # we have at max 5 elements of the dataset wich are superset
        # we take the top-5 elements of misere sampling
        # we pick one sequence, and launch several generalization

        best_patterns = PrioritySetQuality()

        for sequence in node.dataset_sequences:
            # for now we consider this upper bound (try better later)
            items = set([i for j_set in sequence for i in j_set])
            ads = len(items) * (2 * len(sequence) - 1)

            for i in range(int(math.log(ads))):
                subsequence = copy.deepcopy(sequence)

                # we remove z items randomly, if they are not in the intersection
                # between expanded_node and sursequences
                forbiden_itemsets = subsequence_indices(node.sequence, sequence)

                seq_items_nb = len([i for j_set in subsequence for i in j_set])
                z = random.randint(1, seq_items_nb - 2)

                subsequence = sequence_immutable_to_mutable(subsequence)

                for _ in range(z):
                    chosen_itemset_i = random.randint(0, len(subsequence) - 1)
                    chosen_itemset = subsequence[chosen_itemset_i]

                    # here we check if chosen_itemset is not a forbidden one.
                    if chosen_itemset_i not in forbiden_itemsets:
                        chosen_itemset.remove(random.sample(chosen_itemset, 1)[0])

                        if len(chosen_itemset) == 0:
                            subsequence.pop(chosen_itemset_i)

                created_node = SequenceNode(subsequence, None,
                                            self.items, self.data,
                                            self.target_class,
                                            self.target_class_data_count,
                                            self.enable_i)

                best_patterns.add(created_node)

        top_k_patterns = best_patterns.get_top_k(5)

        for i in top_k_patterns:
            self.sorted_patterns.add(i[1])

        mean_quality = sum([i[0] for i in top_k_patterns]) / len(
            top_k_patterns)

        return mean_quality

    def update(self, node, reward):
        """
        Backtrack: update the node and recursively update all nodes until the root
        :param node: the node we want to update
        :param reward: the reward we got
        :return: None
        """
        # mean-update
        node.update(reward)

        for parent in node.parents:
            if parent != None:
                self.update(parent, reward)

    def best_child(self, node):
        """
        Return the best child, based on UCT. Can only return a child which is
        not a dead_end
        :param node:
        :return: the best child, or None if we reached a dead_end
        """
        best_node = None
        max_score = -float("inf")

        for child in node.generated_children:
            current_uct = uct(node, child)
            if current_uct > max_score and not child.is_dead_end:
                max_score = current_uct
                best_node = child

        return best_node

    def explore_children(self, node, sorted_patterns):
        """
        Find children of node and add them to sorted_children
        :param node: the parent from which we explore children
        :param sorted_patterns: PrioritySetQuality.
        :return: None
        """
        for child in node.generated_children:
            sorted_patterns.add(child)
            self.explore_children(child, sorted_patterns)


# TODO: command line interface, with pathfile of data, number of patterns and max_time
if __name__ == '__main__':
    DATA = read_data('../data/promoters.data')

    items = extract_items(DATA)

    mcts = MCTSeq(5, items, DATA, 5, '+',
                  enable_i=False)
    result = mcts.launch()
    print_results_mcts(result)
