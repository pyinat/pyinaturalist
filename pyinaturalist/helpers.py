# For Python < 3.5 compatibility
def merge_two_dicts(x, y):
    z = x.copy()
    z.update(y)
    return z
