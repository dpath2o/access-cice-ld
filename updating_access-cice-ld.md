# Updating `access-cice-ld` (patch + provenance workflow)

This document records the **milestone-based** workflow for keeping the `dpath2o/access-cice-ld` repository up to date **without** disrupting the active Spack dev association in the `om3_cice6_dev` environment.

## Goals

* Keep local dev in **`~/AFIM/src/access-cice`** (this is what Spack `develop:` points to).
* Publish **milestone snapshots** to `access-cice-ld` as:

  * a **patch series** (easy for others to apply/PR), and
  * **provenance** (Spack env, specs, key run inputs).
* Avoid “mirroring every commit”; update only when something is worth sharing/reproducing.

## Key paths (assumptions)

* **Dev code (Spack `develop:` path):**

  * `~/AFIM/src/access-cice`
* **Patch/provenance repo:**

  * `~/AFIM/src/access-cice-ld`
* **Spack environment:**

  * `/g/data/gv90/da1339/spack/0.22/environments/om3_cice6_dev`

> Publishing patches/docs to `access-cice-ld` does **not** affect Spack, as long as you do not move or rename `~/AFIM/src/access-cice` and do not change the `develop:` stanza in the Spack env.

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

In your dev repo (`~/AFIM/src/access-cice`), determine the base commit **relative to upstream**.

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

### How others apply your patches

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

## Step 6 — build/test loop (local)

### When you change code in `~/AFIM/src/access-cice`:

* If you need a new executable, rebuild via Spack (this is **your** local loop).
* Only update `access-cice-ld` at milestones.

Typical cycle:

```bash
# edit code in ~/AFIM/src/access-cice

# rebuild (or reinstall) the dependent stack as needed
spack -e /g/data/gv90/da1339/spack/0.22/environments/om3_cice6_dev install -j 16 --fail-fast

# then run your payu smoke test / 1993–1994 test
```

---

## Guardrails (do not break Spack dev association)

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
