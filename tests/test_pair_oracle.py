from itertools import combinations

from app.modules.pairs.optimal import best_pairs


def test_optimal_score_agrees_with_all_small_monotone_mappings():
    for left,right in [([1,5,7],[0,2,6,8]), ([0,5],[0,0,7]), ([],[1,2]), ([2,2],[3,3,4])]:
        for gap in range(5):
            scores = [(0,0)]
            for count in range(1,min(len(left),len(right))+1):
                for ix in combinations(range(len(left)),count):
                    for iy in combinations(range(len(right)),count):
                        spans = [abs(left[x]-right[y]) for x,y in zip(ix,iy)]
                        if max(spans) <= gap:
                            scores.append((count,-sum(spans)))
            actual = best_pairs(left,right,gap)
            assert (len(actual),-sum(abs(left[x]-right[y]) for x,y in actual)) == max(scores)
