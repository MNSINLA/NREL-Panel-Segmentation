#!/usr/bin/env python3
"""Proof-of-concept batch extractor for mounting structure + geometry fields.

This script orchestrates existing Panel-Segmentation pipelines and keeps
new logic focused on:
- batch I/O
- result mapping
- error handling and logging

It intentionally reuses existing core methods instead of reimplementing them.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from shapely import wkt as shapely_wkt

from panel_segmentation import PanelDetection
from panel_segmentation.lidar import PCD, PlaneSegmentation, USGSLidarAPI


OUTPUT_COLUMNS = [
    "site_id",
    "latitude",
    "longitude",
    "image_path",
    "raw_mount_labels",
    "raw_mount_scores",
    "top_mount_label",
    "structure_single_axis",
    "structure_fixed",
    "azimuth_angle_image",
    "lidar_available",
    "tilt_angle_lidar",
    "azimuth_angle_lidar",
    "status",
    "notes",
]

FIXED_LABELS = {"ground-fixed", "rooftop-fixed", "carport-fixed"}
SINGLE_AXIS_LABEL = "ground-single_axis_tracker"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Batch PoC for mounting type and geometry extraction.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--input-csv",
        default="data/poc_sites_template.csv",
        help="Input CSV with columns: site_id, latitude, longitude (+optional polygon_wkt).",
    )
    parser.add_argument(
        "--output-csv",
        default="outputs/poc_results.csv",
        help="Output CSV path.",
    )
    parser.add_argument(
        "--outputs-dir",
        default="outputs",
        help="Folder for generated images and intermediate LiDAR artifacts.",
    )
    parser.add_argument(
        "--google-maps-api-key",
        default=None,
        help="Google Maps Static API key. Required if --generate-images is set.",
    )
    parser.add_argument(
        "--generate-images",
        action="store_true",
        help="Generate site satellite images using PanelDetection.generateSatelliteImage().",
    )
    parser.add_argument(
        "--existing-image-dir",
        default=None,
        help=(
            "Optional folder of pre-downloaded PNG files named '<site_id>.png'. "
            "Used when --generate-images is not set."
        ),
    )
    parser.add_argument(
        "--lidar-metadata-parquet",
        default="panel_segmentation/lidar/data/master_usgs_lidar_metadata.parquet",
        help="Master USGS LiDAR metadata parquet used by locateLazFileByLatLon().",
    )
    parser.add_argument(
        "--lat-lon-bbox-size",
        type=int,
        default=20,
        help="BBox size in meters for LiDAR crop when polygon_wkt is not provided.",
    )
    parser.add_argument(
        "--mount-acc-cutoff",
        type=float,
        default=0.65,
        help="Confidence cutoff passed into classifyMountingConfiguration().",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity.",
    )
    return parser.parse_args()


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s %(levelname)s %(message)s",
    )


def get_site_image_path(
    site_id: str,
    latitude: float,
    longitude: float,
    panel_detection: PanelDetection,
    outputs_dir: Path,
    generate_images: bool,
    google_maps_api_key: Optional[str],
    existing_image_dir: Optional[Path],
) -> Tuple[Optional[Path], str]:
    """Resolve (or generate) image path for a site."""
    if generate_images:
        if not google_maps_api_key:
            return None, "--generate-images requires --google-maps-api-key"
        image_path = outputs_dir / f"{site_id}_raw.png"
        panel_detection.generateSatelliteImage(
            float(latitude),
            float(longitude),
            str(image_path),
            google_maps_api_key,
        )
        return image_path, ""

    if existing_image_dir:
        image_path = existing_image_dir / f"{site_id}.png"
    else:
        image_path = outputs_dir / f"{site_id}_raw.png"

    if image_path.exists():
        return image_path, ""
    return None, (
        f"Site image not found at {image_path}. "
        "Provide --existing-image-dir or use --generate-images."
    )


def compute_image_outputs(
    panel_detection: PanelDetection,
    image_path: Path,
    site_id: str,
    outputs_dir: Path,
    mount_acc_cutoff: float,
) -> Dict[str, Any]:
    """Run existing mounting + image azimuth pipelines and map outputs."""
    mount_annotated_path = outputs_dir / f"{site_id}_mounting.png"
    azimuth_overlay_path = outputs_dir / f"{site_id}_azimuth_overlay.png"

    scores, labels, _ = panel_detection.classifyMountingConfiguration(
        image_file_path=str(image_path),
        acc_cutoff=mount_acc_cutoff,
        file_name_save=str(mount_annotated_path),
    )

    # Reuse the existing image azimuth pipeline (includes tracker adjustment).
    analysis = panel_detection.runSiteAnalysisPipeline(
        file_name_save_img=str(image_path),
        file_name_save_mount=str(mount_annotated_path),
        file_path_save_azimuth=str(azimuth_overlay_path),
        generate_image=False,
    )

    score_floats = [float(s) for s in scores]
    label_list = list(labels)
    top_label = label_list[0] if label_list else None

    azimuths = analysis.get("associated_azimuths", []) or []
    image_azimuth = float(azimuths[0]) if len(azimuths) > 0 else None

    return {
        "image_path": str(image_path),
        "raw_mount_labels": json.dumps(label_list),
        "raw_mount_scores": json.dumps(score_floats),
        "top_mount_label": top_label,
        "structure_single_axis": any(lbl == SINGLE_AXIS_LABEL for lbl in label_list),
        "structure_fixed": any(lbl in FIXED_LABELS for lbl in label_list),
        "azimuth_angle_image": image_azimuth,
    }


def maybe_parse_polygon_wkt(row: pd.Series) -> Any:
    polygon_wkt = row.get("polygon_wkt", None)
    if pd.isna(polygon_wkt) or polygon_wkt is None or str(polygon_wkt).strip() == "":
        return None
    return shapely_wkt.loads(str(polygon_wkt))


def compute_lidar_outputs(
    row: pd.Series,
    lidar_api: USGSLidarAPI,
    metadata_df: pd.DataFrame,
    lat_lon_bbox_size: int,
) -> Dict[str, Any]:
    """Run existing LiDAR pipeline and return best-plane tilt/azimuth."""
    latitude = float(row["latitude"])
    longitude = float(row["longitude"])
    polygon = maybe_parse_polygon_wkt(row)

    laz_link = lidar_api.locateLazFileByLatLon(metadata_df, latitude, longitude)
    if laz_link is None:
        return {
            "lidar_available": False,
            "tilt_angle_lidar": None,
            "azimuth_angle_lidar": None,
            "notes": "No USGS LiDAR link found for site coordinates.",
        }

    laz_file_path = lidar_api.downloadLazFile(laz_link)

    if polygon is not None:
        pcd_reader = PCD(str(laz_file_path), polygon=polygon)
    else:
        pcd_reader = PCD(str(laz_file_path), latitude=latitude, longitude=longitude)

    laz_data = pcd_reader.readLaz()
    filtered = pcd_reader.filterLaz(
        laz_data,
        classification_list=[1, 6],
        lat_lon_bbox_size=lat_lon_bbox_size,
    )
    if filtered is None:
        return {
            "lidar_available": False,
            "tilt_angle_lidar": None,
            "azimuth_angle_lidar": None,
            "notes": "LiDAR exists but no points after crop/class filter.",
        }

    pcd = pcd_reader.preprocessPcd(filtered, nb_neighbors=10, std_ratio=0.5)
    if pcd is None:
        return {
            "lidar_available": False,
            "tilt_angle_lidar": None,
            "azimuth_angle_lidar": None,
            "notes": "LiDAR exists but preprocessing returned empty point cloud.",
        }

    plane_seg = PlaneSegmentation(pcd)
    plane_seg.segmentPlanes(
        distance_threshold=1.0,
        ransac_n=3,
        num_ransac_iterations=5000,
        min_plane_points=3,
        max_num_planes=10,
    )
    plane_seg.mergeSimilarPlanes(tilt_diff_threshold=5.0, azimuth_diff_threshold=10.0)

    best_plane, found_best_plane = plane_seg.getBestPlane()
    if not found_best_plane or best_plane is None:
        return {
            "lidar_available": False,
            "tilt_angle_lidar": None,
            "azimuth_angle_lidar": None,
            "notes": "LiDAR exists but no usable plane found.",
        }

    return {
        "lidar_available": True,
        "tilt_angle_lidar": float(best_plane.get("tilt")),
        "azimuth_angle_lidar": float(best_plane.get("azimuth")),
        "notes": "",
    }


def process_site(
    row: pd.Series,
    panel_detection: PanelDetection,
    lidar_api: USGSLidarAPI,
    metadata_df: pd.DataFrame,
    outputs_dir: Path,
    generate_images: bool,
    google_maps_api_key: Optional[str],
    existing_image_dir: Optional[Path],
    lat_lon_bbox_size: int,
    mount_acc_cutoff: float,
) -> Dict[str, Any]:
    site_id = str(row["site_id"])
    latitude = float(row["latitude"])
    longitude = float(row["longitude"])

    result: Dict[str, Any] = {
        "site_id": site_id,
        "latitude": latitude,
        "longitude": longitude,
        "image_path": None,
        "raw_mount_labels": "[]",
        "raw_mount_scores": "[]",
        "top_mount_label": None,
        "structure_single_axis": False,
        "structure_fixed": False,
        "azimuth_angle_image": None,
        "lidar_available": False,
        "tilt_angle_lidar": None,
        "azimuth_angle_lidar": None,
        "status": "ok",
        "notes": "",
    }

    notes: List[str] = []

    # Image + mounting + image azimuth
    try:
        image_path, image_note = get_site_image_path(
            site_id=site_id,
            latitude=latitude,
            longitude=longitude,
            panel_detection=panel_detection,
            outputs_dir=outputs_dir,
            generate_images=generate_images,
            google_maps_api_key=google_maps_api_key,
            existing_image_dir=existing_image_dir,
        )
        if image_note:
            notes.append(image_note)
        if image_path is not None:
            image_result = compute_image_outputs(
                panel_detection=panel_detection,
                image_path=image_path,
                site_id=site_id,
                outputs_dir=outputs_dir,
                mount_acc_cutoff=mount_acc_cutoff,
            )
            result.update(image_result)
        else:
            result["status"] = "partial"
    except Exception as exc:  # noqa: BLE001 - keep per-site failures graceful
        logging.exception("Image pipeline failed for site_id=%s", site_id)
        result["status"] = "partial"
        notes.append(f"Image pipeline failed: {exc}")

    # LiDAR
    try:
        lidar_result = compute_lidar_outputs(
            row=row,
            lidar_api=lidar_api,
            metadata_df=metadata_df,
            lat_lon_bbox_size=lat_lon_bbox_size,
        )
        result.update({k: v for k, v in lidar_result.items() if k != "notes"})
        if lidar_result.get("notes"):
            notes.append(str(lidar_result["notes"]))
    except Exception as exc:  # noqa: BLE001 - keep per-site failures graceful
        logging.exception("LiDAR pipeline failed for site_id=%s", site_id)
        result["status"] = "partial"
        notes.append(f"LiDAR pipeline failed: {exc}")

    # Final status
    if result["status"] != "partial" and (result["image_path"] is None or not result["lidar_available"]):
        result["status"] = "partial"
    if result["image_path"] is None and not result["lidar_available"]:
        result["status"] = "failed"

    result["notes"] = " | ".join([n for n in notes if n]).strip()
    return result


def main() -> None:
    args = parse_args()
    setup_logging(args.log_level)

    input_csv = Path(args.input_csv)
    output_csv = Path(args.output_csv)
    outputs_dir = Path(args.outputs_dir)
    existing_image_dir = Path(args.existing_image_dir) if args.existing_image_dir else None

    outputs_dir.mkdir(parents=True, exist_ok=True)
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    logging.info("Reading input CSV: %s", input_csv)
    sites_df = pd.read_csv(input_csv)

    required_cols = {"site_id", "latitude", "longitude"}
    missing = required_cols - set(sites_df.columns)
    if missing:
        raise ValueError(f"Input CSV missing required columns: {sorted(missing)}")

    logging.info("Loading models/pipelines...")
    panel_detection = PanelDetection()
    lidar_api = USGSLidarAPI(output_folder=str(outputs_dir))

    metadata_df = pd.read_parquet(args.lidar_metadata_parquet)

    rows: List[Dict[str, Any]] = []
    total = len(sites_df)
    for idx, row in sites_df.iterrows():
        site_id = row.get("site_id")
        logging.info("Processing site %s (%s/%s)", site_id, idx + 1, total)
        row_result = process_site(
            row=row,
            panel_detection=panel_detection,
            lidar_api=lidar_api,
            metadata_df=metadata_df,
            outputs_dir=outputs_dir,
            generate_images=args.generate_images,
            google_maps_api_key=args.google_maps_api_key,
            existing_image_dir=existing_image_dir,
            lat_lon_bbox_size=args.lat_lon_bbox_size,
            mount_acc_cutoff=args.mount_acc_cutoff,
        )
        rows.append(row_result)

    result_df = pd.DataFrame(rows)
    for col in OUTPUT_COLUMNS:
        if col not in result_df.columns:
            result_df[col] = None
    result_df = result_df[OUTPUT_COLUMNS]

    result_df.to_csv(output_csv, index=False)
    logging.info("Wrote results: %s", output_csv)


if __name__ == "__main__":
    main()
