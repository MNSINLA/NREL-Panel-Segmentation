# Notebooks Guide

This file summarizes what each notebook in this repository is meant to do.

## Panel Detection

### `docs/examples/panel_detection/Panel_Detection_example.ipynb`

Purpose:
- Starts from a single latitude/longitude site.
- Pulls a satellite image for that site.
- Detects solar panels in the image.
- Groups detections into installations.
- Estimates mounting configuration and azimuth/orientation for the detected arrays.

Use this notebook when:
- You want to analyze one site at a time.
- You care about panel grouping and orientation metadata, not just detection locations.

Notes:
- Requires Google Maps Static API if you want to download a fresh image.
- This is the notebook that estimates azimuth.

### `docs/examples/panel_detection/Sol-Searcher_example.ipynb`

Purpose:
- Starts from a geographic bounding box.
- Downloads a grid of satellite tiles across that area.
- Runs solar-panel detection over the whole grid.
- Converts detections into latitude/longitude points.
- Reverse-geocodes those detections into addresses.
- Aggregates detections by address and shows them on a map.

Use this notebook when:
- You want to search an area for likely solar installations.
- You care about where systems are and which addresses they belong to.

Notes:
- Requires Google Maps Static API to download imagery.
- Requires Google Geocoding API for address lookup.
- This notebook is about finding and geolocating systems, not estimating azimuth.

### `docs/examples/panel_detection/Train_Model_Example.ipynb`

Purpose:
- Demonstrates how to train the panel-detection model.
- Uses the package's training pipeline around a VGG16-based setup.

Use this notebook when:
- You want to retrain or experiment with the detection model.

## Automated Geotagging

### `docs/examples/automated_geotagging/automated_geotagging_fixed_tilt_site.ipynb`

Purpose:
- Runs the automated geotagging pipeline on a fixed-tilt utility PV site.
- Isolates equipment/features across the site and aggregates them into geospatial outputs.

Primary output:
- GeoJSON-style site equipment data for mapping and downstream analysis.

### `docs/examples/automated_geotagging/automated_geotagging_tracking_site.ipynb`

Purpose:
- Runs the automated geotagging pipeline on a tracker-based utility PV site.
- Focuses on identifying tracker rows and inverters across a large site.

Primary output:
- Geospatially tagged equipment/features for the whole PV site.

## Extreme Weather

### `docs/examples/extreme_weather/Austin_hail_damage_example.ipynb`

Purpose:
- Detects hail damage on solar installations from satellite imagery.
- Uses example Austin-area hail data bundled with the repo.

Use this notebook when:
- You want to evaluate hail-event damage on PV systems.

### `docs/examples/extreme_weather/Hurricane_damage_example.ipynb`

Purpose:
- Detects hurricane damage on solar installations from satellite imagery.

Use this notebook when:
- You want to evaluate storm-related PV damage after a hurricane event.

## LiDAR

### `docs/examples/lidar/LiDAR_Tilt_Azimuth_Estimation_Example.ipynb`

Purpose:
- Uses satellite-image inference masks plus LiDAR data to estimate solar panel tilt and azimuth.
- Pulls the relevant `.laz` file, crops the point cloud, fits planes, and merges similar planes.

Use this notebook when:
- You want geometry estimates derived from LiDAR instead of image-only inference.

### `docs/examples/lidar/USGS_LiDAR_API_Example.ipynb`

Purpose:
- Demonstrates the repository's USGS LiDAR API helper.
- Looks up available datasets, metadata, and the `.laz` file covering a latitude/longitude.

Use this notebook when:
- You want to find or inspect LiDAR coverage before running the full LiDAR workflow.

## MESH Scan

### `docs/examples/mesh_scan/MESH_scan_example.ipynb`

Purpose:
- Downloads NOAA MESH hail data.
- Converts the GRIB2 weather data into contours and polygons.
- Exports the result to KML and GeoJSON.
- Calculates areas for hail ranges.

Use this notebook when:
- You want geospatial hail-footprint products rather than PV-specific detection outputs.

## Other Notebook

### `notebooks/poc_mounting_geometry.ipynb`

Purpose:
- Wrapper notebook for `scripts/poc_mounting_geometry.py`.
- Runs batch mounting/geometry extraction from an input CSV of sites.

Use this notebook when:
- You want to run the batch proof-of-concept workflow from notebook cells instead of calling the script directly.

## Quick Correction

The two panel-detection notebooks are easy to mix up:

- `Panel_Detection_example.ipynb`:
  single site, panel grouping, mounting configuration, azimuth/orientation.
- `Sol-Searcher_example.ipynb`:
  area search, panel detections across many tiles, lat/lon extraction, address lookup, mapping.

## API Key Reminder

Some notebooks contain Google API keys inline while being explored locally. Do not commit real keys to version control.
