def best_pairs(left, right, tolerance):
    """Maximize pairs before minimizing total absolute separation on ordered lists."""
    n, m = len(left), len(right)
    scores = [[(0, 0)] * (m+1) for _ in range(n+1)]
    choices = [bytearray(m) for _ in range(n)]
    for i in range(n-1, -1, -1):
        for j in range(m-1, -1, -1):
            skip_right, skip_left = scores[i][j+1], scores[i+1][j]
            score, choice = (skip_right, 1) if skip_right >= skip_left else (skip_left, 2)
            delta = abs(left[i] - right[j])
            if delta <= tolerance:
                count, neg_distance = scores[i+1][j+1]
                matched = (count+1, neg_distance-delta)
                if matched >= score:
                    score, choice = matched, 3
            scores[i][j], choices[i][j] = score, choice
    i = j = 0
    pairs = []
    while i < n and j < m:
        choice = choices[i][j]
        if choice == 3:
            pairs.append((i, j))
        i += choice in (2,3)
        j += choice in (1,3)
    return pairs
