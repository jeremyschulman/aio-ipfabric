from itertools import chain


def callback_csv_list(ctx, param, value):  # noqa
    names = list()

    for expr in chain(value):
        names.extend(expr.split(","))

    return names
