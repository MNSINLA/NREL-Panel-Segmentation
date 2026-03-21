# AGENTS.md

## Notebook Environment

- Prefer `python -m pip install -e . --no-deps` when linking this repo into the active virtual environment.
- A plain `pip install -e .` may downgrade `typing_extensions` to `4.5.0` through the TensorFlow 2.13 dependency chain.
- If that happens, Jupyter kernels may fail at startup because `IPython`/`ipykernel` expects `typing_extensions.TypeAliasType`.

Use the repair helper from the repo root:

```bat
scripts\repair_notebook_env.bat
```

This restores the editable install without re-resolving dependencies and then reinstalls `typing_extensions==4.15.0`.

## MMCV On Windows

- `Sol-Searcher_example.ipynb` needs `mmcv` in addition to `mmdet`.
- On this setup, `mmcv` source install failed until `setuptools` was pinned below 81 so `pkg_resources` remained available.
- The working sequence was:

```bat
python -m pip install --force-reinstall "setuptools<81"
python -m pip install --no-build-isolation git+https://github.com/open-mmlab/mmcv.git@v2.1.0
python -c "import mmcv; print(mmcv.__version__)"
```

- The `mmcv` wheel build can take a while on Windows. Slow progress during `Building wheel for mmcv` is normal.
- After any dependency churn, rerun `scripts\repair_notebook_env.bat` if notebook kernels stop starting.

## Sol-Searcher Checkpoint

- The SOL-Searcher notebook should not manually call `torch.load()` on `panel_segmentation/models/sol_searcher_model.pth`.
- That checkpoint hit NumPy serialization compatibility issues in this environment (`numpy._core` / `structseq.c` failures).
- Prefer:

```python
import importlib
import sys
sys.modules.setdefault("numpy._core", importlib.import_module("numpy.core"))
sys.modules.setdefault("numpy._core.multiarray", importlib.import_module("numpy.core.multiarray"))
sys.modules.setdefault("numpy._core.numeric", importlib.import_module("numpy.core.numeric"))
sys.modules.setdefault("numpy._core._multiarray_umath", importlib.import_module("numpy.core._multiarray_umath"))
model = init_detector(cfg, checkpoint_file, device='cpu')
```

- This PyTorch build does not expose `torch.serialization.load_module_mapping`; patch `sys.modules` instead.
- If this notebook regresses to manual `torch.load(...)`, expect checkpoint-loading failures or hard kernel exits.

## Notebook Warnings

- This setup pins `setuptools<81` for `mmcv`, which can trigger a `pkg_resources is deprecated as an API` warning from `dash`.
- That warning is incidental for these notebooks. Suppress it in notebook import cells rather than changing the environment again.

## HTTPS Warning

- The Google Maps static image request paths in `panel_segmentation/panel_detection.py` and `panel_segmentation/utils.py` should not use `verify=False`.
- If an insecure HTTPS warning reappears, confirm the environment is importing code from this checkout rather than an older installed copy.

Sanity check:

```bat
python -c "import panel_segmentation.panel_detection as pd; print(pd.__file__)"
```
