from typing import Iterable, List


def get_unique_elems_ordered(iterable: Iterable[str]) -> List[str]:
    unique_items = []
    for item in iterable:
        if item not in unique_items:
            unique_items += [item]
    return unique_items