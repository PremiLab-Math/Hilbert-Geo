# Hilbert-Geo

This repository is reorganized into three main parts so the reasoning core, model APIs, and sample data are no longer mixed together.

## Structure

```text
SolidGeoSolver/
├── api/
│   ├── base.py
│   ├── claude_api.py
│   ├── gemini_api.py
│   └── openai_api.py
├── core/
│   ├── fgps/
│   ├── gdl/
│   ├── files/
│   └── hilbert_geo/
└── data/
    └── hilbert_geo_sample_1k/
```

- `api/` contains prompt-and-call helpers for model APIs.
  The prompt templates in `api/base.py` are adapted from the supplementary material appendix `C.4 Prompt Templates`.
- `core/hilbert_geo/` is the renamed FormalGeo package.
- `core/gdl/` and `core/files/t_info.json` keep the predicate bank, theorem bank, and theorem metadata with the core code.
- `data/hilbert_geo_sample_1k/` contains a 1k sample subset for repository display and quick testing.

## Quick Start

Install dependencies:

```bash
pip install -r requirements.txt
```

And download the Hilbert-Geo core package separately

Run the interactive solver:

```bash
python core/fgps/run.py --func run
```

Run search:

```bash
python core/fgps/search.py --func search --method fw --strategy bfs
```

By default:

- datasets are loaded from `data/`
- logs are written to `core/fgps/`
- GDL and theorem metadata are loaded from `core/` when they are not present in the dataset folder

## Notes

- The Python package name is now `hilbert_geo`.
- The repository display name used in docs is `Hilbert-Geo`.
- The sample dataset folder is renamed to `hilbert_geo_sample_1k` and only includes the first 1000 problems.
