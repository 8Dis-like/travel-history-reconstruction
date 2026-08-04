from __future__ import annotations


def test_all_predictions_in_correct_order_scores_one():
    from src.reconstruction.scene_eval import pairwise_order_accuracy
    pairs = [("2019-01-01", "2019-01-01"), ("2020-01-01", "2020-06-06"), ("2021-01-01", "2021-01-01")]
    assert pairwise_order_accuracy(pairs) == 1.0


def test_fully_reversed_predictions_score_zero():
    from src.reconstruction.scene_eval import pairwise_order_accuracy
    pairs = [("2019-01-01", "2021-01-01"), ("2020-01-01", "2020-01-01"), ("2021-01-01", "2019-01-01")]
    assert pairwise_order_accuracy(pairs) == 0.0


def test_one_swapped_pair_scores_partially():
    from src.reconstruction.scene_eval import pairwise_order_accuracy
    # true order A<B<C ; predicted swaps B and C -> pair (B,C) discordant, others fine
    pairs = [("2019-01-01", "2019-01-01"), ("2020-01-01", "2021-12-31"), ("2021-01-01", "2020-01-01")]
    assert pairwise_order_accuracy(pairs) == 2 / 3


def test_unparseable_predicted_date_makes_its_pairs_discordant():
    from src.reconstruction.scene_eval import pairwise_order_accuracy
    pairs = [("2019-01-01", None), ("2020-01-01", "2020-01-01")]
    assert pairwise_order_accuracy(pairs) == 0.0


def test_equal_true_dates_are_not_counted():
    from src.reconstruction.scene_eval import pairwise_order_accuracy
    # only one comparable pair (the equal-true one is excluded); it is concordant
    pairs = [("2020-01-01", "2020-01-01"), ("2020-01-01", "2020-01-01"), ("2021-01-01", "2021-06-06")]
    assert pairwise_order_accuracy(pairs) == 1.0


def test_fewer_than_two_comparable_pairs_scores_one():
    from src.reconstruction.scene_eval import pairwise_order_accuracy
    assert pairwise_order_accuracy([]) == 1.0
    assert pairwise_order_accuracy([("2020-01-01", "2020-01-01")]) == 1.0
