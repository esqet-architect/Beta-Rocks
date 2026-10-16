"""
Command-line interface.

Subcommands:
    preflight       Run the hardware preflight report.
    spot            Run a spot magnetic survey.
    grid            Run a grid survey.
    transect        Run a transect survey.
    identify        Run a candidate identification against a reference pack.
    phi             Compute phi deviation for a pair of lengths.
    shape           Describe a 2D silhouette from a JSON landmark file.
    import-lidar    Register a LiDAR/DEM/vector dataset.
    install-pack    Install a reference pack.
    attribution     Print attribution for a reference pack.
"""
import argparse
import json
import os
import sys

from .hardware import run_preflight, format_preflight_report
from .hardware.lidar import LidarDevice
from .survey import run_spot_survey, run_grid_survey, run_transect_survey
from .analysis.phi_ratio import analyze_pair
from .analysis.shape import describe_shape
from .references.reference_pack_importer import install_pack
from .references.source_attribution import format_attributions


def _cmd_preflight(args) -> int:
    work_dir = args.work_dir or os.path.join(os.path.expanduser("~"), "fieldwork")
    report = run_preflight(work_dir, log_dir=work_dir)
    print(format_preflight_report(report))
    return 0


def _cmd_spot(args) -> int:
    obs = run_spot_survey(
        specimen_id=args.specimen_id,
        specimen_dir=args.specimen_dir,
        samples=args.samples,
        gps_visibility=args.visibility,
    )
    print(json.dumps(obs, indent=2))
    return 0


def _cmd_grid(args) -> int:
    summary = run_grid_survey(
        specimen_id=args.specimen_id,
        specimen_dir=args.specimen_dir,
        rows=args.rows,
        cols=args.cols,
        spacing_m=args.spacing,
        gps_visibility=args.visibility,
    )
    print(json.dumps(summary, indent=2))
    return 0


def _cmd_transect(args) -> int:
    summary = run_transect_survey(
        specimen_id=args.specimen_id,
        specimen_dir=args.specimen_dir,
        points=args.points,
        spacing_m=args.spacing,
        gps_visibility=args.visibility,
    )
    print(json.dumps(summary, indent=2))
    return 0


def _cmd_phi(args) -> int:
    result = analyze_pair(
        name_a=args.name_a,
        length_a=args.length_a,
        name_b=args.name_b,
        length_b=args.length_b,
        uncertainty_a=args.uncertainty_a,
        uncertainty_b=args.uncertainty_b,
    )
    print(json.dumps(result, indent=2))
    return 0


def _cmd_shape(args) -> int:
    with open(args.landmarks) as f:
        data = json.load(f)
    points = data["points"] if isinstance(data, dict) else data
    points = [tuple(p) for p in points]
    result = describe_shape(points)
    print(json.dumps(result, indent=2))
    return 0


def _cmd_import_lidar(args) -> int:
    dev = LidarDevice()
    result = dev.import_dataset(
        args.path, source=args.source, crs=args.crs, datum=args.datum
    )
    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1


def _cmd_install_pack(args) -> int:
    result = install_pack(args.pack_dir, args.target_db)
    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1


def _cmd_attribution(args) -> int:
    path = os.path.join(args.pack_dir, "attributions.json")
    if not os.path.exists(path):
        print("No attributions.json found in pack directory.")
        return 1
    with open(path) as f:
        records = json.load(f)
    print(format_attributions(records))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="fossil-scan", description="FossilScanner CLI")
    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("preflight", help="Run hardware preflight")
    sp.add_argument("--work-dir", default=None)
    sp.set_defaults(func=_cmd_preflight)

    sp = sub.add_parser("spot", help="Spot magnetic survey")
    sp.add_argument("--specimen-id", default=None)
    sp.add_argument("--specimen-dir", required=True)
    sp.add_argument("--samples", type=int, default=15)
    sp.add_argument("--visibility", choices=("exact", "generalized", "withheld"), default="exact")
    sp.set_defaults(func=_cmd_spot)

    sp = sub.add_parser("grid", help="Grid magnetic survey")
    sp.add_argument("--specimen-id", default=None)
    sp.add_argument("--specimen-dir", required=True)
    sp.add_argument("--rows", type=int, required=True)
    sp.add_argument("--cols", type=int, required=True)
    sp.add_argument("--spacing", type=float, required=True)
    sp.add_argument("--visibility", choices=("exact", "generalized", "withheld"), default="exact")
    sp.set_defaults(func=_cmd_grid)

    sp = sub.add_parser("transect", help="Transect magnetic survey")
    sp.add_argument("--specimen-id", default=None)
    sp.add_argument("--specimen-dir", required=True)
    sp.add_argument("--points", type=int, required=True)
    sp.add_argument("--spacing", type=float, required=True)
    sp.add_argument("--visibility", choices=("exact", "generalized", "withheld"), default="exact")
    sp.set_defaults(func=_cmd_transect)

    sp = sub.add_parser("phi", help="Phi deviation between two lengths")
    sp.add_argument("--name-a", required=True)
    sp.add_argument("--length-a", type=float, required=True)
    sp.add_argument("--name-b", required=True)
    sp.add_argument("--length-b", type=float, required=True)
    sp.add_argument("--uncertainty-a", type=float, default=0.0)
    sp.add_argument("--uncertainty-b", type=float, default=0.0)
    sp.set_defaults(func=_cmd_phi)

    sp = sub.add_parser("shape", help="Describe a 2D silhouette")
    sp.add_argument("--landmarks", required=True, help="JSON file with points")
    sp.set_defaults(func=_cmd_shape)

    sp = sub.add_parser("import-lidar", help="Register a LiDAR/DEM/vector dataset")
    sp.add_argument("--path", required=True)
    sp.add_argument("--source", default="")
    sp.add_argument("--crs", default="")
    sp.add_argument("--datum", default="")
    sp.set_defaults(func=_cmd_import_lidar)

    sp = sub.add_parser("install-pack", help="Install a reference pack")
    sp.add_argument("--pack-dir", required=True)
    sp.add_argument("--target-db", required=True)
    sp.set_defaults(func=_cmd_install_pack)

    sp = sub.add_parser("attribution", help="Print pack attributions")
    sp.add_argument("--pack-dir", required=True)
    sp.set_defaults(func=_cmd_attribution)

    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
