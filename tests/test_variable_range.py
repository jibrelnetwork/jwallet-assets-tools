from jwallet_tools.blockexplorer.blockrange import VariableBlockRange


def test_range():
    ranger = VariableBlockRange(0, 0)
    assert next(iter(ranger)) == (0, 0)

    ranger = VariableBlockRange(0, 100, batch_size=50)
    res = list(ranger)
    assert len(res) == 3
    assert res == [(0, 49), (50, 99), (100, 100)]

    ranger = VariableBlockRange(0, 100, batch_size=60)
    res = list(ranger)
    assert len(res) == 2
    assert res == [(0, 59), (60, 100)]

    ranger = VariableBlockRange(0, 100, batch_size=30)
    res = list(ranger)
    assert len(res) == 4
    assert res == [(0, 29), (30, 59), (60, 89), (90, 100)]


def test_set_step():
    instance = VariableBlockRange(0, 100, batch_size=50)
    ranger = iter(instance)
    assert next(ranger) == (0, 49)
    instance.set_step(10)
    assert next(ranger) == (50, 59)
    assert next(ranger) == (60, 69), "Seems like reset flag wasn't reset"


def test_change_range():
    instance = VariableBlockRange(0, 100, batch_size=50)
    ranger = iter(instance)
    assert next(ranger) == (0, 49)
    instance.set_step(10)
    assert next(ranger) == (50, 59)
    instance.set_step(20)
    instance.rollback()
    assert next(ranger) == (50, 69)


def test_reverse_range():
    ranger = VariableBlockRange(0, 100, reverse=True, batch_size=50)
    res = list(ranger)
    assert res == [(51, 100), (1, 50), (1, 1)]


def test_rollback():
    ranger = VariableBlockRange(0, 100, reverse=True, batch_size=50)
    it = iter(ranger)
    assert next(it) == (51, 100)
    ranger.rollback()
    assert next(it) == (51, 100)
    assert next(it) == (1, 50)


def test_reverse_change_range():
    ranger = VariableBlockRange(0, 100, reverse=True, batch_size=50)
    it = iter(ranger)
    assert next(it) == (51, 100)
    ranger.set_step(10)
    assert next(it) == (41, 50)
