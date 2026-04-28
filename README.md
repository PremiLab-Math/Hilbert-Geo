<p align="center">
  <h1 style="display: inline-block; font-size: 24px; text-align: center; line-height: 1.5;"> 
    <img src="./logo.png" alt="Logo" style="width: 45px; vertical-align: middle; margin-right: 10px;"> 
    Hilbert-Geo: Solving Solid Geometric Problems<br>
    <span style="display: block; text-align: center; margin-left: -55px; padding-top: 4px;">
              by Neural-Symbolic Reasoning
    </span>
  </h1>
</p>

<p align="center">
  <a href="https://github.com/PremiLab-Math/Hilbert-Geo"> 🏷️ New Repository
</p>

## News

<div style="max-height: 350px; overflow-y: auto; border: 1px solid #e0e0e0; border-radius: 8px; padding: 10px 15px; background-color: #fafafa; font-size: 12px;" markdown="1">
2026.02: &nbsp;🎉🎉 Our paper "Hilbert-Geo: Solving Solid Geometric Problems by Neural-Symbolic Reasoning" was accepted by CVPR2026.
</div>

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
    └── hilbert_geo_v2/
```

- `api/` contains prompt-and-call helpers for model APIs.
- `core/hilbert_geo/` is the package.
- `core/gdl/` and `core/files/t_info.json` keep the predicate library, theorem bank, and theorem metadata with the core code.
- `data/hilbert_geo_v2/` contains sample subset for repository display and quick testing. https://github.com/CHYYYYYYYY/SolidGeoSolver/tree/main/data/hilbert_geo7k_v2

## Quick Start

Install dependencies, you may need to manually download hilbertgeo in requirement.txt at present:

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
- The sample dataset folder is renamed to `hilbert_geo_v2` and only includes the first 1000 problems.

## ✍️ Citation
If you use our work and are inspired by our work, please consider cite us (soon):
```
@inproceedings{xu2026hilbert,
  title={Hilbert-Geo: Solving Solid Geometric Problems by Neural-Symbolic Reasoning},
  author={Xu, Ruoran and Cheng, Haoyu and Bin, Dong and Wang, Qiufeng},
  booktitle={Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)},
  pages={XXXX--XXXX},
  year={2026},
  doi={10.XXXX/CVPR2026.XXXXXX},
  url={https://openaccess.thecvf.com/CVPR2026}
}
```
