from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
DATA_ROOT = PROJECT_ROOT / "data"
LOG_ROOT = CORE_ROOT / "fgps"
DEFAULT_DATASET_NAME = "hilbert_geo7k_v2"
