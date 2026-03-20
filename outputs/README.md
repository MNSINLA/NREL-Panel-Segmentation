# PoC Mounting + Geometry Outputs

This folder is used by `scripts/poc_mounting_geometry.py` for generated artifacts.

## Produced files

- `poc_results.csv`: final batch output table.
- `{site_id}_raw.png`: raw satellite image used for inference.
- `{site_id}_mounting.png`: mounting-classification annotated image from `PanelDetection.classifyMountingConfiguration()`.
- `{site_id}_azimuth_overlay.png`: azimuth overlay image from `PanelDetection.runSiteAnalysisPipeline()`.
- `lidar_laz/*.laz`: downloaded USGS LiDAR files (when available).

## Final CSV schema (`outputs/poc_results.csv`)

- `site_id`
- `latitude`
- `longitude`
- `image_path`
- `raw_mount_labels` (JSON list)
- `raw_mount_scores` (JSON list)
- `top_mount_label`
- `structure_single_axis`
- `structure_fixed`
- `azimuth_angle_image`
- `lidar_available`
- `tilt_angle_lidar`
- `azimuth_angle_lidar`
- `status`
- `notes`

## Mapping used in the script

- `structure_single_axis = True` if any detected mount label is `ground-single_axis_tracker`.
- `structure_fixed = True` if any detected mount label is in:
  - `ground-fixed`
  - `rooftop-fixed`
  - `carport-fixed`

## Example command

```bash
python scripts/poc_mounting_geometry.py \
  --input-csv data/poc_sites_template.csv \
  --output-csv outputs/poc_results.csv \
  --outputs-dir outputs \
  --existing-image-dir outputs
```

To generate fresh satellite images, add:

```bash
--generate-images --google-maps-api-key "<YOUR_KEY>"
```
