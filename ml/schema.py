"""Input schema shared by prediction services and integrations."""

from src.preprocessing import FEATURES, NUMERICAL_FEATURES, CATEGORICAL_FEATURES, TARGET

REQUIRED_FEATURES = tuple(FEATURES)

__all__ = ["FEATURES", "NUMERICAL_FEATURES", "CATEGORICAL_FEATURES", "TARGET", "REQUIRED_FEATURES"]
