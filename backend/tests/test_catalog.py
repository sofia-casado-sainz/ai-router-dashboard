from router.catalog import MODELS, ModelId
from router.model_selector import FALLBACK_RULE, ROUTING_RULES


def test_every_model_id_is_in_catalog() -> None:
    assert set(MODELS) == set(ModelId)
    assert all(model.id == model_id for model_id, model in MODELS.items())


def test_every_routing_rule_targets_a_catalog_model() -> None:
    for rule in (*ROUTING_RULES, FALLBACK_RULE):
        assert rule.model_id in MODELS
