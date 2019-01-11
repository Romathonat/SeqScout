import datetime
import random
import copy
import math
import os

from seqehc.utils import read_data, read_data_kosarak, uct, \
    is_subsequence, sequence_mutable_to_immutable, print_results, \
    read_data_sc2, k_length, generate_bitset, following_ones, \
    get_support_from_vector, compute_first_zero_mask, compute_last_ones_mask, \
    count_target_class_data, extract_items, compute_WRAcc, compute_WRAcc_vertical, jaccard_measure

from seqehc.priorityset import PrioritySet, THETA


def compute_random_variations(sequence, items, data, target_class,
                              bitset_slot_size,
                              itemsets_bitsets, class_data_count,
                              first_zero_mask,
                              last_ones_mask, enable_i=False,
                              ):
    '''
    Compute a random number of random variations of sequence
    '''

    number_max_variations = len(items) * (2 * len(sequence) + 1)

    number_variations = random.randint(1, number_max_variations)
    variations = []
    for i in range(number_variations):
        # we compute randomly a s, i-extension or remove element

        if enable_i:
            choice = random.sample({'i', 's', 'remove'}, 1)[0]
        else:
            choice = random.sample({'s', 'remove'}, 1)[0]

        if choice == 'i':
            new_variation_i_extension = copy.deepcopy(sequence)
            new_variation_i_extension[
                random.randint(0, len(sequence) - 1)].add(
                random.sample(items, 1)[0])
            new_variation_i_wracc, _ = compute_WRAcc_vertical(data,
                                                              new_variation_i_extension,
                                                              target_class,
                                                              bitset_slot_size,
                                                              itemsets_bitsets,
                                                              class_data_count,
                                                              first_zero_mask,
                                                              last_ones_mask)

            variations.append(
                (new_variation_i_extension, new_variation_i_wracc))
        elif choice == 's':
            new_variation_s_extension = copy.deepcopy(sequence)
            new_variation_s_extension.insert(random.randint(0, len(sequence)),
                                             set(random.sample(items, 1)[0]))
            new_variation_s_wracc, _ = compute_WRAcc_vertical(data,
                                                              new_variation_s_extension,
                                                              target_class,
                                                              bitset_slot_size,
                                                              itemsets_bitsets,
                                                              class_data_count,
                                                              first_zero_mask,
                                                              last_ones_mask)
            variations.append(
                (new_variation_s_extension, new_variation_s_wracc))

        else:
            new_variation_remove = copy.deepcopy(sequence)
            random_index = random.randint(0, len(sequence) - 1)

            if (k_length(sequence) > 1):
                new_variation_remove[random_index].remove(
                    random.sample(sequence[random_index], 1)[0])
                if len(new_variation_remove[random_index]) == 0:
                    new_variation_remove.pop(random_index)

                new_variation_remove_wracc, _ = compute_WRAcc_vertical(data,
                                                                       new_variation_remove,
                                                                       target_class,
                                                                       bitset_slot_size,
                                                                       itemsets_bitsets,
                                                                       class_data_count,
                                                                       first_zero_mask,
                                                                       last_ones_mask)
                variations.append(
                    (new_variation_remove, new_variation_remove_wracc))

    if len(variations) > 0:
        return variations
    else:
        return compute_random_variations(sequence, items,
                                         data, target_class,
                                         bitset_slot_size,
                                         itemsets_bitsets,
                                         class_data_count,
                                         first_zero_mask,
                                         last_ones_mask,
                                         enable_i)


def compute_variations(sequence, items, data, target_class,
                       bitset_slot_size,
                       itemsets_bitsets, class_data_count, first_zero_mask,
                       last_ones_mask, enable_i=False,
                       horizontal_var=False):
    '''
    Compute all variations with one step, with the WRAcc
    :param sequence:
    :param items: the list of all possible items
    :return: the variations, with their wracc in the form [(sequence, wracc), (..., ...), ...]
    '''
    variations = []

    for itemset_i, itemset in enumerate(sequence):
        # i_extension
        if enable_i:
            for item_possible in items:
                new_variation_i_extension = copy.deepcopy(sequence)
                new_variation_i_extension[itemset_i].add(item_possible)


                new_variation_i_wracc, new_variation_i_bitset = compute_WRAcc_vertical(data,
                                                                                       new_variation_i_extension,
                                                                                       target_class,
                                                                                       bitset_slot_size,
                                                                                       itemsets_bitsets,
                                                                                       class_data_count,
                                                                                       first_zero_mask,
                                                                                       last_ones_mask)

                variations.append(
                    (new_variation_i_extension, new_variation_i_wracc, new_variation_i_bitset))

        # s_extension
        for item_possible in items:
            new_variation_s_extension = copy.deepcopy(sequence)
            new_variation_s_extension.insert(itemset_i, {item_possible})

            new_variation_s_wracc, new_variation_s_bitset = compute_WRAcc_vertical(data,
                                                                                   new_variation_s_extension,
                                                                                   target_class,
                                                                                   bitset_slot_size,
                                                                                   itemsets_bitsets,
                                                                                   class_data_count,
                                                                                   first_zero_mask,
                                                                                   last_ones_mask)

            variations.append(
                (new_variation_s_extension, new_variation_s_wracc, new_variation_s_bitset))

        for item_i, item in enumerate(itemset):
            new_variation_remove = copy.deepcopy(sequence)

            # we can switch this item, remove it or add it as s or i-extension

            if (k_length(sequence) > 1):
                new_variation_remove[itemset_i].remove(item)

                if len(new_variation_remove[itemset_i]) == 0:
                    new_variation_remove.pop(itemset_i)

                new_variation_remove_wracc, new_variation_remove_bitset = compute_WRAcc_vertical(
                    data,
                    new_variation_remove,
                    target_class,
                    bitset_slot_size,
                    itemsets_bitsets,
                    class_data_count,
                    first_zero_mask,
                    last_ones_mask)

                variations.append(
                    (new_variation_remove, new_variation_remove_wracc, new_variation_remove_bitset))

            if horizontal_var:
                for item_possible in items:
                    new_variation = copy.deepcopy(sequence)
                    new_variation[itemset_i].remove(item)
                    new_variation[itemset_i].add(item_possible)
                    new_variation_wracc, new_variation_bitset = compute_WRAcc_vertical(data,
                                                                                       new_variation,
                                                                                       target_class,
                                                                                       bitset_slot_size,
                                                                                       itemsets_bitsets,
                                                                                       class_data_count,
                                                                                       first_zero_mask,
                                                                                       last_ones_mask)

                    variations.append((new_variation, new_variation_wracc, new_variation_bitset))

    # s_extension for last element
    for item_possible in items:
        new_variation_s_extension = copy.deepcopy(sequence)
        new_variation_s_extension.append({item_possible})

        new_variation_s_wracc, new_variation_s_bitset = compute_WRAcc_vertical(data,
                                                                               new_variation_s_extension,
                                                                               target_class,
                                                                               bitset_slot_size,
                                                                               itemsets_bitsets,
                                                                               class_data_count,
                                                                               first_zero_mask,
                                                                               last_ones_mask)
        variations.append(
            (new_variation_s_extension, new_variation_s_wracc, new_variation_s_bitset))

    return variations


def compute_variations_better_wracc(sequence, items, data, target_class,
                                    bitset_slot_size,
                                    itemsets_bitsets, class_data_count,
                                    first_zero_mask,
                                    last_ones_mask, target_wracc,
                                    enable_i=False):
    '''
    Compute variations until quality increases
    :param sequence:
    :param items: the list of all possible items
    :return: the variations, with their wracc in the form [(sequence, wracc), (..., ...), ...]
    '''
    variations = []

    for itemset_i, itemset in enumerate(sequence):
        # i_extension
        if enable_i:
            for item_possible in items:
                new_variation_i_extension = copy.deepcopy(sequence)
                new_variation_i_extension[itemset_i].add(item_possible)

                new_variation_i_wracc, _ = compute_WRAcc_vertical(data,
                                                                  new_variation_i_extension,
                                                                  target_class,
                                                                  bitset_slot_size,
                                                                  itemsets_bitsets,
                                                                  class_data_count,
                                                                  first_zero_mask,
                                                                  last_ones_mask)

                variations.append(
                    (new_variation_i_extension, new_variation_i_wracc))

                if new_variation_i_wracc > target_wracc:
                    return variations

        # s_extension
        for item_possible in items:
            new_variation_s_extension = copy.deepcopy(sequence)
            new_variation_s_extension.insert(itemset_i, {item_possible})

            new_variation_s_wracc, _ = compute_WRAcc_vertical(data,
                                                              new_variation_s_extension,
                                                              target_class,
                                                              bitset_slot_size,
                                                              itemsets_bitsets,
                                                              class_data_count,
                                                              first_zero_mask,
                                                              last_ones_mask)

            variations.append(
                (new_variation_s_extension, new_variation_s_wracc))

            if new_variation_s_wracc > target_wracc:
                return variations

        for item_i, item in enumerate(itemset):
            new_variation_remove = copy.deepcopy(sequence)

            # we can switch this item, remove it or add it as s or i-extension

            if (k_length(sequence) > 1):
                new_variation_remove[itemset_i].remove(item)

                if len(new_variation_remove[itemset_i]) == 0:
                    new_variation_remove.pop(itemset_i)

                new_variation_remove_wracc, _ = compute_WRAcc_vertical(data,
                                                                       new_variation_remove,
                                                                       target_class,
                                                                       bitset_slot_size,
                                                                       itemsets_bitsets,
                                                                       class_data_count,
                                                                       first_zero_mask,
                                                                       last_ones_mask)

                variations.append(
                    (new_variation_remove, new_variation_remove_wracc))
                if new_variation_remove_wracc > target_wracc:
                    return variations

    # s_extension for last element
    for item_possible in items:
        new_variation_s_extension = copy.deepcopy(sequence)
        new_variation_s_extension.append({item_possible})

        new_variation_s_wracc, _ = compute_WRAcc_vertical(data,
                                                          new_variation_s_extension,
                                                          target_class,
                                                          bitset_slot_size,
                                                          itemsets_bitsets,
                                                          class_data_count,
                                                          first_zero_mask,
                                                          last_ones_mask)

        variations.append(
            (new_variation_s_extension, new_variation_s_wracc))
        if new_variation_s_wracc > target_wracc:
            return variations

    return variations


def generalize_sequence(sequence, data, target_class, bitset_slot_size,
                        itemsets_bitsets, class_data_count,
                        first_zero_mask,
                        last_ones_mask) :
    sequence = copy.deepcopy(sequence)
    # we remove z items randomly
    seq_items_nb = len([i for j_set in sequence for i in j_set])
    z = random.randint(0, seq_items_nb - 1)
    for _ in range(z):
        chosen_itemset_i = random.randint(0, len(sequence) - 1)
        chosen_itemset = sequence[chosen_itemset_i]

        chosen_itemset.remove(random.sample(chosen_itemset, 1)[0])

        if len(chosen_itemset) == 0:
            sequence.pop(chosen_itemset_i)

    # now we compute the Wracc
    wracc, bitset = compute_WRAcc_vertical(data, sequence, target_class,
                                           bitset_slot_size,
                                           itemsets_bitsets, class_data_count,
                                           first_zero_mask, last_ones_mask)

    return sequence, wracc, bitset


def filter_target_class(data, target_class):
    filter_data = []
    for line in data:
        if line[0] == target_class:
            filter_data.append(line)

    return filter_data


def extract_best_elements_path(path, theta, bitset_slot_size, first_zero_mask, last_ones_mask):
    '''

    :param path: path in the form of (WRAcc, sequence, bitset)
    :param theta: similarity
    :return:
    '''
    try:
        best_wracc, best_sequence, best_bitset = path[-1]
    except:
        return []

    best_sequences = [(best_wracc, best_sequence)]

    # need to compare with each previous added element
    for wracc, sequence, bitset in reversed(path):
        if jaccard_measure(bitset, best_bitset, bitset_slot_size, first_zero_mask, last_ones_mask) < theta:
            best_sequences.append((wracc, sequence))
            best_sequence, best_bitset = sequence, bitset

    return best_sequences


def misere_hill(data, items, time_budget, target_class, top_k=10,
                enable_i=False, horizontale_var=False,
                ):
    begin = datetime.datetime.utcnow()
    time_budget = datetime.timedelta(seconds=time_budget)

    data_target_class = filter_target_class(data, target_class)

    sorted_patterns = PrioritySet(top_k)

    # removing class
    bitset_slot_size = len(max(data, key=lambda x: len(x))) - 1

    first_zero_mask = compute_first_zero_mask(len(data), bitset_slot_size)
    last_ones_mask = compute_last_ones_mask(len(data), bitset_slot_size)
    class_data_count = count_target_class_data(data, target_class)
    itemsets_bitsets = {}

    iteration_count = 0

    while datetime.datetime.utcnow() - begin < time_budget:
        sequence = copy.deepcopy(random.choice(data_target_class))
        sequence = sequence[1:]

        current_sequence, current_wracc, current_bitset = generalize_sequence(sequence,
                                                                              data,
                                                                              target_class,
                                                                              bitset_slot_size,
                                                                              itemsets_bitsets,
                                                                              class_data_count,
                                                                              first_zero_mask,
                                                                              last_ones_mask)
        stored_path = []

        while 'climbing hill':
            # we compute all possible variations

            variations = compute_variations(current_sequence, items, data,
                                            target_class,
                                            bitset_slot_size,
                                            itemsets_bitsets,
                                            class_data_count,
                                            first_zero_mask,
                                            last_ones_mask,
                                            enable_i=enable_i,
                                            horizontal_var=horizontale_var)
            '''
            variations = compute_random_variations(current_sequence, items,
                                                   data, target_class,
                                                   bitset_slot_size,
                                                   itemsets_bitsets,
                                                   class_data_count,
                                                   first_zero_mask,
                                                   last_ones_mask,
                                                   enable_i)
            '''
            '''
            variations = compute_variations_better_wracc(current_sequence, items,
                                                   data, target_class,
                                                   bitset_slot_size,
                                                   itemsets_bitsets,
                                                   class_data_count,
                                                   first_zero_mask,
                                                   last_ones_mask,
                                                   current_wracc,
                                                   enable_i=enable_i)
            '''
            # we take the best solution, and we iterate
            sequence, wracc, bitset = max(variations, key=lambda x: x[1])

            if wracc > current_wracc:
                current_sequence = sequence
                current_wracc = wracc
                current_bitset = bitset
                stored_path.append((wracc, sequence, bitset))
            else:
                break

        # add best element of the path
        best_elements = extract_best_elements_path(stored_path, THETA, bitset_slot_size, first_zero_mask, last_ones_mask)
        for wracc, sequence in best_elements:
            sorted_patterns.add(sequence_mutable_to_immutable(sequence), wracc)

        # sorted_patterns.add(sequence_mutable_to_immutable(current_sequence), current_wracc)

        iteration_count += 1

    print('Misere_hill iterations:{}'.format(iteration_count))

    return sorted_patterns.get_top_k_non_redundant(data, top_k)


def launch():
    DATA = read_data_sc2('../data/sequences-TZ-45.txt')[:100]
    # DATA = read_data_kosarak('../data/debile.data')

    ITEMS = extract_items(DATA)
    # DATA = read_data_kosarak('../data/all.csv')
    results = misere_hill(DATA, ITEMS, 10, '1', enable_i=True)
    print_results(results)


if __name__ == '__main__':
    launch()