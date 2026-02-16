# Updating access-cice-ld: end-to-end workflow (Spack build ➜ Payu run ➜ GitHub)

This document records the **milestone-based** workflow for keeping the `dpath2o/access-cice-ld` repository up to date **without** disrupting the active Spack dev association in the `om3_cice6_dev` environment.

This is the repeatable workflow I’m using to:

1. develop CICE6 changes in `~/AFIM/src/access-cice` (*free-slip* + *lateral-drag*, etc.),
2. rebuild the coupled ACCESS-OM3 executable via Spack (`om3_cice6_dev`),
3. run a payu experiment (ACCESS-OM3 configs), including swapping in a zeroed-ice CICE IC,
4. publish my modified `payu` control directory via my GitHub fork.

This note records the “edit → rebuild → run” loop for developing `access-cice` (CICE6.6.1) inside a Spack environment (`om3_cice6_dev`) and testing it in a standard ACCESS‑OM3 payu control directory (e.g. `release-MC_25km_jra_iaf`).

> **Key idea**: your **payu control directory** (the cloned config, containing `config.yaml`, `ice_in`, `nuopc.runconfig`, `manifests/*`) is what you version/share for experiments.
> Your **source tree** (`~/AFIM/src/access-cice`) is what you edit.
> Your **Spack env** builds the binaries that the payu run uses.

## Goals

+ Local dev in **`~/AFIM/src/access-cice`** (this is what Spack `develop:` points to).
+ Publish **milestone snapshots** to `access-cice-ld` as:

  + a **patch series** (easy for others to apply/PR), and
  + **provenance** (Spack env, specs, key run inputs).

+ Avoid “mirroring every commit”; update only when something is worth sharing/reproducing.

## Key paths (assumptions)

* **Run code (ACCESS-OM3) path/repo:**

    +`~/access-om3`

* **Dev code (Spack `develop:` path):**

    + `~/AFIM/src/access-cice`

* **Patch/provenance repo:**

    + `~/AFIM/src/access-cice-ld`

* **Spack environment:**

    + `/g/data/gv90/da1339/spack/0.22/environments/om3_cice6_dev`

> Publishing patches/docs to `access-cice-ld` does **not** affect Spack, as long as you do not move or rename `~/AFIM/src/access-cice` and do not change the `develop:` stanza in the Spack env.

## Helpful info

The **control directory** is the directory you `payu clone` and then edit:

* contains: `config.yaml`, `ice_in`, `nuopc.runconfig`, `input.nml`, `manifests/*`, etc.
* example: `~/access-om3/25km_jra_iaf_ld/`

It is **not**:

* the Spack tree (`/g/data/gv90/da1339/spack/0.22/...`)
* the source tree (`~/AFIM/src/access-cice`)


---

## When to update `access-cice-ld`

Update at **milestones**, e.g.

* ✅ Spack/OM3 build completes cleanly
* ✅ First coupled smoke test runs (short wallclock)
* ✅ First clean 1993–1994 run completes
* ✅ Any change to **namelist interface** (new keys, changed defaults)
* ✅ Any change to **file inputs** (new F2 file, new IC handling)
* ✅ Before sharing with ACCESS-NRI (or creating a PR upstream)

Between milestones: keep hacking locally; rebuild Spack as needed.

---

## Repository structure (recommended)

In `access-cice-ld`, keep:

* `patches/`

  * `BASE.sha`
  * `HEAD.sha`
  * `0001-...patch`, `0002-...patch`, ...
* `provenance/`

  * `spack.yaml`
  * `spack.lock`
  * `spec_access-om3.txt`
  * `spack_find.txt`
  * `access-cice_git_head.txt`
  * `access-cice_git_status.txt`
  * `run_inputs.md` (paths to ICs, F2, ice_in deltas, config branch)
* `README.md`

  * short “Reproduce” section (apply patches → build → smoke test)

---

## Step 0 — one-time setup of `access-cice-ld`

If `access-cice-ld` is empty or newly created:

```bash
cd ~/AFIM/src

git clone git@github.com:dpath2o/access-cice-ld.git
cd access-cice-ld

mkdir -p patches provenance
```

---

## Step 1 — identify upstream base commit for patching

In dev repo (`~/AFIM/src/access-cice`), determine the base commit **relative to upstream**.

```bash
cd ~/AFIM/src/access-cice

git remote -v

# Determine upstream default branch name (e.g. main/master)
DEFAULT_BRANCH=$(git remote show origin | sed -n 's/  HEAD branch: //p')

echo "Upstream default branch: ${DEFAULT_BRANCH}"

# Find the merge-base between upstream and your current HEAD
BASE=$(git merge-base origin/${DEFAULT_BRANCH} HEAD)

echo "BASE=${BASE}"

git show -s --format='%H %ci %s' ${BASE}
```

This `BASE` is what others will apply your patch series against.

---

## Step 2 — export a clean patch series at a milestone

This overwrites the previous patch series in `access-cice-ld/patches/`.

```bash
cd ~/AFIM/src/access-cice

DEFAULT_BRANCH=$(git remote show origin | sed -n 's/  HEAD branch: //p')
BASE=$(git merge-base origin/${DEFAULT_BRANCH} HEAD)

PATCHDIR=~/AFIM/src/access-cice-ld/patches

# Clean old patch exports
rm -f ${PATCHDIR}/*.patch ${PATCHDIR}/BASE.sha ${PATCHDIR}/HEAD.sha

# Export patches
mkdir -p ${PATCHDIR}
git format-patch -o ${PATCHDIR} ${BASE}..HEAD

# Record provenance of the patch range
git rev-parse ${BASE} > ${PATCHDIR}/BASE.sha
git rev-parse HEAD    > ${PATCHDIR}/HEAD.sha

# Commit to access-cice-ld
cd ~/AFIM/src/access-cice-ld

git add patches

git commit -m "Milestone: update patch series ($(cut -c1-8 patches/HEAD.sha))" || true

git push
```

### How others can apply my patches

```bash
# starting from an upstream clone at BASE.sha (or a compatible point)
git am patches/*.patch
```

---

## Step 3 — capture build provenance (Spack)

Store Spack environment artifacts and the concretized dependency tree.

```bash
cd ~/AFIM/src/access-cice-ld
ENV=/g/data/gv90/da1339/spack/0.22/environments/om3_cice6_dev
mkdir -p provenance
# Environment files
cp -v ${ENV}/spack.yaml provenance/spack.yaml
cp -v ${ENV}/spack.lock provenance/spack.lock
# Concretized spec (load-bearing for reproducibility)
spack -e ${ENV} spec -Il access-om3 > provenance/spec_access-om3.txt
# What is installed + where
spack -e ${ENV} find -p > provenance/spack_find.txt
```

Optional (useful when debugging):

```bash
spack -e ${ENV} config blame | head -n 200 > provenance/spack_config_blame_head.txt
```

From anywhere (on a Gadi login / dm node), activate your Spack and env:

```bash
source /g/data/gv90/da1339/spack/0.22/spack/share/spack/setup-env.sh
spack env activate -p /g/data/gv90/da1339/spack/0.22/environments/om3_cice6_dev
```

### Option 3.1 — rebuild only `access-cice`

Use this if you only changed CICE code and want the dependency rebuilt:

```bash
spack -e /g/data/gv90/da1339/spack/0.22/environments/om3_cice6_dev install -f access-cice
spack -e /g/data/gv90/da1339/spack/0.22/environments/om3_cice6_dev view regenerate
```

### Option 3.2 — rebuild the whole coupled executable (`access-om3`)

Use this if you changed something that may require relinking, or you want to be certain everything is consistent:

```bash
spack -e /g/data/gv90/da1339/spack/0.22/environments/om3_cice6_dev install -f access-om3
spack -e /g/data/gv90/da1339/spack/0.22/environments/om3_cice6_dev view regenerate
```

### Check what executable your environment provides

```bash
spack load access-om3
command -v access-om3-MOM6-CICE6
# should point into your env’s view, e.g.
# /g/data/gv90/da1339/spack/0.22/environments/om3_cice6_dev/.spack-env/view/bin/access-om3-MOM6-CICE6
```

---

## Step 4 — capture code identity of your dev repo

```bash
cd ~/AFIM/src/access-cice
git log -1 --decorate --oneline > ~/AFIM/src/access-cice-ld/provenance/access-cice_git_head.txt
git status > ~/AFIM/src/access-cice-ld/provenance/access-cice_git_status.txt
```

---

## Step 5 — capture runtime inputs (what matters for replication)

Create/update `provenance/run_inputs.md` to record:

* OM3 config repo + branch (e.g. `release-MC_25km_jra_iaf`)
* Start/stop dates (1993–1994)
* MOM6 IC path
* CICE IC path (zeroed ice)
* `ice_in` modifications (either full file, or `diff` vs stock config)
* Lateral-drag / free-slip settings
* Form factor file path + variable names + mapping method

Example skeleton:

```markdown
# Runtime inputs (milestone YYYY-MM-DD)

## Config
- access-om3-configs branch/tag: ...
- control dir: ...

## Clocks
- start: 1993-01-01
- stop: 1994-12-31

## MOM6
- IC: ~/AFIM_input/mom/ic/ocean_temp_salt.res.nc (copied from /g/data/vk83/...)

## CICE6
- IC (zeroed ice): ~/AFIM_input/cice/ic/iced_zero.nc (derived from /g/data/vk83/...)
- ice_in: path + notes / diff

## Lateral drag / free-slip
- boundary_condition = 'free-slip'
- lateral_drag = .true.
- form_func = '...'
- coefficients: ...

## F2 form factors
- F2_file: ...
- varnames: F2x=..., F2y=...
- mapping: F2_map_method = ...
```

Commit these provenance updates:

```bash
cd ~/AFIM/src/access-cice-ld
git add provenance
git commit -m "Update provenance for milestone ($(date -I))" || true
git push
```

---

## 6) Stage a *zeroed-ice* CICE initial condition

### 6.1 Put iced file somewhere stable

Prefer `/g/data/...` over `/home/...` for I/O reliability.

Example:

```bash
mkdir -p /g/data/gv90/da1339/afim_input/cice/ic
cp -v /g/data/vk83/configurations/inputs/access-om3/cice/initial_conditions/global.025deg/2024.04.09/iced.1900-01-01-10800.nc \
      /g/data/gv90/da1339/afim_input/cice/ic
```

### 6.2 zero the file

```bash
module use /g/data/xp65/public/modules/
module load conda/analysis3-26.02
cd ~/AFIM/access-cice-ld/
python prep_zero_ice_cice_ic.py
```

### 6.3 Ensure `ice_in` *actually reads* the file

In `ice_in`:

```fortran
&setup_nml
  ice_ic = './INPUT/iced.1900-01-01-10800.nc'
/
```

(If `ice_ic='none'`, CICE will not read an IC file.)

### 6.3 Make payu stage the file and update manifests

Add the file to `config.yaml` input list (control dir):

```yaml
input:
  - /g/data/gv90/da1339/afim_input/cice/ic/iced.1900-01-01-10800.nc
  # ... the rest of the config inputs
```

If you are using `manifest.reproduce.input: True`, payu will **refuse** to run until the manifest is updated to include this new file.

---

## 7) add form factors

Add the file to `config.yaml` input list (control dir):

```yaml
input:
    - /g/data/gv90/da1339/coastal_drag/form_factors/ADD_high-res_cstln_v7p9_GI.nc
  # ... the rest of the config inputs
```

Then in `ice_in`:

```fortran
&grid_nml
  F2_file         = './INPUT/ADD_high-res_cstln_v7p9_GI.nc'
  F2x_varname     = 'F2x'
  F2y_varname     = 'F2y'
  F2_map_method   = 'max'  
/
```

## 9) other `ice_in` edits

## 10) Updating payu manifests cleanly (avoids “Run cannot reproduce”)

When adding/removing inputs or change `exe:`, do this once:

1. temporarily disable reproduce checks
2. re-run `payu setup` to regenerate manifests
3. re-enable reproduce

This is the most direct approach. After each rebuild, the path stays valid as long as you regenerate the env view.

### hardwire `exe:`

In `config.yaml` (control dir):

```yaml
exe: /g/data/gv90/da1339/spack/0.22/environments/om3_cice6_dev/.spack-env/view/bin/access-om3-MOM6-CICE6
```

### activate Spack on the compute node

Create `userscripts/spack_setup.sh` in the control dir:

```bash
#!/usr/bin/env bash
set -euo pipefail
source /g/data/gv90/da1339/spack/0.22/spack/share/spack/setup-env.sh
spack env activate -p /g/data/gv90/da1339/spack/0.22/environments/om3_cice6_dev
spack load access-om3
echo "Using executable:" $(command -v access-om3-MOM6-CICE6)
```

Then in `config.yaml`:

```yaml
userscripts:
  setup: /usr/bin/bash -lc "./userscripts/spack_setup.sh"
  archive: /usr/bin/bash /g/data/vk83/apps/om3-scripts/payu_config/archive.sh
```

### Getting new input files to be *manifested*

#### Disable reproduce temporarily

In `config.yaml`:

```yaml
manifest:
  reproduce:
    exe: False
    input: False
```

#### Clear the existing work directory

```bash
payu sweep
```

#### Run setup again to regenerate manifests

```bash
payu setup
```

Now `manifests/input.yaml` and/or `manifests/exe.yaml` should include the new staged items.

#### Re-enable reproduce once stable

```yaml
manifest:
  reproduce:
    exe: True
    input: True
```

Commit the updated manifests into your fork/branch if you want strict reproducibility.

---

## 11) run

```bash
payu setup
payu run
```

Watch `log/` for first‑step failures. For your initial test, keep the configuration default (B‑grid, EVP `kdyn=1`, `boundary_condition='no_slip'`) and just validate:

* your new code compiles/links in coupled mode
* your new namelist keys are accepted
* outputs write cleanly

Once stable, then flip:

```fortran
boundary_condition = 'free-slip'
lateral_drag       = .true.
```

---

## 12) GitHub workflow: keep code and configs separate

* Put **CICE code** changes in your `access-cice` repo/branch.
* Put **payu control‑dir config** changes in a fork of `access-om3-configs` (what you already did).

That keeps ACCESS‑NRI’s workflow happy: they can review your config PR separately from your code PR.
---

## 13) Guardrails (do not break Spack dev association)

Do **not**:

* move/rename `~/AFIM/src/access-cice`
* change the `develop:` stanza in `om3_cice6_dev` unless you mean to
* convert your dev repo into a detached tarball without updating Spack

Safe to do:

* create/update `access-cice-ld` as docs + patches only
* add provenance files
* tag milestone commits in `access-cice-ld`

---

## Optional: tagging milestones in `access-cice-ld`

```bash
cd ~/AFIM/src/access-cice-ld

git tag -a milestone-2026-02-13 -m "First coupled build with LD + free-slip"

git pu
```
