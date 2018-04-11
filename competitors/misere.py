import datetime
import random
import copy
import math

from mctseq.utils import read_data, extract_items, uct, \
    is_subsequence, sequence_mutable_to_immutable
from mctseq.priorityset import PrioritySet


def compute_WRAcc(data, subsequence, target_class):
    subsequence_supp = 0
    data_supp = len(data)
    target_subsequence_supp = 0
    target_data_supp = 0
    for sequence in data:
        current_class = sequence[1]
        sequence = sequence[1:]

        if is_subsequence(subsequence, sequence):
            subsequence_supp += 1
            if current_class == target_class:
                target_subsequence_supp += 1

        if current_class == target_class:
            target_data_supp += 1

    return (subsequence_supp / data_supp) * (
            target_subsequence_supp / subsequence_supp -
            target_data_supp / data_supp)


def misere(data, time_budget, top_k=5):
    begin = datetime.datetime.utcnow()
    time_budget = datetime.timedelta(seconds=time_budget)

    # patterns with
    sorted_patterns = PrioritySet()

    while datetime.datetime.utcnow() - begin < time_budget:
        sequence = copy.deepcopy(random.choice(data))
        target_class = sequence[0]
        sequence = sequence[1:]

        # for now we consider this upper bound (try better later)
        items = set([i for j_set in sequence[1:] for i in j_set])
        ads = len(items) * (2 * len(sequence) - 1)

        for i in range(int(math.log(ads))):
            subsequence = copy.deepcopy(sequence)

            # we remove z items randomly
            seq_items_nb = len([i for j_set in subsequence for i in j_set])
            # print(seq_items_nb)
            z = random.randint(1, seq_items_nb - 2)

            for _ in range(z):
                chosen_itemset_i = random.randint(0, len(subsequence) - 1)
                chosen_itemset = subsequence[chosen_itemset_i]

                # print(sequence)
                # print(chosen_itemset)

                chosen_itemset.remove(random.sample(chosen_itemset, 1)[0])

                if len(chosen_itemset) == 0:
                    subsequence.pop(chosen_itemset_i)

            # now we calculate the Wracc

            wracc = compute_WRAcc(data, subsequence, target_class)

            sorted_patterns.add(sequence_mutable_to_immutable(subsequence),
                                wracc)

    return sorted_patterns.get_top_k(top_k)


DATA = read_data('../data/promoters.data')

print(misere(DATA, 5))
