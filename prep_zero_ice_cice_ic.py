#!/usr/bin/env python3
"""
Copy the ACCESS-OM3 CICE restart IC from /g/data/vk83 into ~/AFIM_input/cice/...
then use NCO (ncap2) via system calls to zero-out sea-ice state (no initial ice),
while preserving grid/mask metadata (iceumask, scale_factor).

Usage:
  python3 prep_zero_ice_cice_ic.py

Optional:
  python3 prep_zero_ice_cice_ic.py --src /path/to/iced.nc --dst ~/AFIM_input/cice/ic/iced.nc
  python3 prep_zero_ice_cice_ic.py --verify
  python3 prep_zero_ice_cice_ic.py --dry-run
"""

from __future__ import annotations
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys


DEFAULT_SRC = "/g/data/vk83/configurations/inputs/access-om3/cice/initial_conditions/global.025deg/2024.04.09/iced.1900-01-01-10800.nc"
DEFAULT_DST = "~/AFIM_input/cice/ic/iced.1900-01-01-10800.nc"


NCAP2_EXPR = r"""
aicen=0; vicen=0; vsnon=0;
uvel=0; vvel=0;
Tsfcn=0;
qice001=0; qice002=0; qice003=0; qice004=0;
qsno001=0;
sice001=0; sice002=0; sice003=0; sice004=0;
stress12_1=0; stress12_2=0; stress12_3=0; stress12_4=0;
stressm_1=0; stressm_2=0; stressm_3=0; stressm_4=0;
stressp_1=0; stressp_2=0; stressp_3=0; stressp_4=0;
strocnxT=0; strocnyT=0;
swidf=0; swidr=0; swvdf=0; swvdr=0;
""".strip()


def run(cmd: list[str], dry_run: bool = False) -> None:
    print("+", " ".join(cmd))
    if dry_run:
        return
    subprocess.run(cmd, check=True)


def which_or_die(exe: str) -> None:
    if shutil.which(exe) is None:
        raise RuntimeError(
            f"Required executable not found in PATH: {exe}\n"
            f"On Gadi you may need: module load nco (or ensure NCO is in your spack env)."
        )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=DEFAULT_SRC, help="Source iced restart file (vk83)")
    ap.add_argument("--dst", default=DEFAULT_DST, help="Destination path under ~/AFIM_input/...")
    ap.add_argument("--overwrite", action="store_true", help="Overwrite dst if it exists")
    ap.add_argument("--dry-run", action="store_true", help="Print commands only")
    ap.add_argument("--verify", action="store_true", help="Run quick NCO checks after zeroing")
    args = ap.parse_args()

    src = Path(args.src).expanduser()
    dst = Path(args.dst).expanduser()

    if not src.exists():
        print(f"ERROR: src does not exist: {src}", file=sys.stderr)
        return 2

    dst.parent.mkdir(parents=True, exist_ok=True)

    if dst.exists() and not args.overwrite:
        print(f"ERROR: dst exists (use --overwrite): {dst}", file=sys.stderr)
        return 3

    # Ensure NCO is available
    which_or_die("ncap2")
    if args.verify:
        which_or_die("ncks")

    # Copy
    print(f"Copying:\n  SRC: {src}\n  DST: {dst}")
    if not args.dry_run:
        shutil.copy2(src, dst)

    # Zero fields in-place using ncap2 system call
    # Note: we *do not* touch iceumask or scale_factor
    run(["ncap2", "-O", "-s", NCAP2_EXPR, str(dst), str(dst)], dry_run=args.dry_run)

    if args.verify:
        # Quick checks: print a few values / confirm vars exist
        # (This is intentionally lightweight)
        run(["ncks", "-H", "-C", "-v", "aicen,uvel,vvel,iceumask,scale_factor", str(dst)], dry_run=args.dry_run)

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

