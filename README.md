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
    └── hilbert_geo7k_v2/
```

- `api/` contains prompt-and-call helpers for model APIs.
- `core/hilbert_geo/` is the renamed FormalGeo package.
- `core/gdl/` and `core/files/t_info.json` keep the predicate bank, theorem bank, and theorem metadata with the core code.
- `data/hilbert_geo7k_v2/` contains a 1k sample subset for repository display and quick testing.

## Quick Start

Install dependencies:

```bash
pip install -r requirements.txt
```

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
- The sample dataset folder is renamed to `hilbert_geo7k_v2` and only includes the first 1000 problems.
