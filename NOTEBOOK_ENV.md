# Notebook Environment Notes

This repository's notebook workflow currently has one Windows-specific trap:

- `pip install -e .` may downgrade `typing_extensions` to `4.5.0`
- newer `IPython`/`ipykernel` needs `TypeAliasType`, which is not present there
- result: Jupyter kernels fail before notebook code runs

Use this sequence from the repo root after changing installs:

```bat
python -m pip install -e . --no-deps
python -m pip install --no-deps --force-reinstall typing_extensions==4.15.0
```

Or use the helper:

```bat
scripts\repair_notebook_env.bat
```

Sanity checks:

```bat
python -c "import panel_segmentation.panel_detection as pd; print(pd.__file__)"
python -c "import inspect, panel_segmentation.panel_detection as pd; print('verify=False' in inspect.getsource(pd.PanelDetection.generateSatelliteImage))"
python -c "from typing_extensions import TypeAliasType; print('typing ok')"
```

Expected results:

- `panel_detection.py` resolves to this checkout, not `.venv\Lib\site-packages`
- the `verify=False` check prints `False`
- the typing check prints `typing ok`

## Google Maps API Key

Store the key in a repo-root `.env` file, not in notebook source.

Start from:

```env
GOOGLE_MAPS_API_KEY=YOUR_API_KEY_HERE
```

The checked-in template is [.env.example](C:\Projects\work\my_products\NREL-Panel-Segmentation\.env.example).

The example notebooks now call `load_env_file()` and `require_env("GOOGLE_MAPS_API_KEY")`, so launching Jupyter from the repo root is enough for them to pick up the key.
