from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import MODEL_ABBREVIATIONS, MODEL_CATEGORIES
from image_gen_api import MODELS, MODEL_REGISTRY


def test_krea_2_turbo_is_registered_and_exposed_in_ui():
    model_id = "fal-ai/krea-2/turbo"

    assert model_id in MODEL_REGISTRY
    assert model_id in MODELS
    assert model_id in MODEL_CATEGORIES["Krea"]
    assert MODEL_ABBREVIATIONS["Krea-2 Turbo"] == "Krea 2 Turbo"
