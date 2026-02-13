# Spack build of ACCESS-OM3 (MOM6+CICE6/NUOPC) using my **CICE6-LD** development tree (`om3_cice6_dev`)

This is the exact Spack setup I ran to get to a working `access-om3` build that **pulls `access-cice` from my dev repo** (containing free-slip + lateral-drag + F2 form-factor loading + new `ice_in` switches).

---

## 0) Ensure my `access-cice` working tree is clean and contains the CICE6-LD changes

```bash
cd ~/AFIM/src/access-cice
git status
# should be clean, on my LD/free-slip branch (e.g. port_free_slip_LD_20260212)
```

During porting I had `git am` conflicts; I resolved them and completed/skipped patches until the repo was clean.

---

## 1) Activate the ACCESS-NRI Spack stack + my dev environment

```bash
# Activate environment (key step)
spack env activate -p om3_cice6_dev

# sanity
spack env status
spack env list
```

> Note: this Spack install does **not** have `spack env edit`. I edited the environment by opening `environments/om3_cice6_dev/spack.yaml` directly (or using `spack edit`).

---

## 2) Configure `om3_cice6_dev` environment (`spack.yaml`)

Environment is rooted on `access-om3@git.2025.08.001` and pins all component versions and toolchain (oneAPI 2025.2.0, `target=x86_64_v4`, Sapphire Rapids flags).

Key points:

* `specs:` contains the root package: `access-om3@git.2025.08.001`
* `packages:` pins the component versions (access3, access-mom6, access-cice, etc.)
* `develop:` points **access-cice** to my local repo path so Spack builds from my working tree

Relevant excerpt (matches what I ended up with):

```yaml
spack:
  specs:
  - access-om3@git.2025.08.001

  concretizer:
    unify: true

  view: true

  packages:
    access3:
      require:
      - '@2025.08.000'
      - configurations=MOM6,MOM6-CICE6,MOM6-CICE6-WW3
      - fflags="-march=sapphirerapids -mtune=sapphirerapids -unroll"
      - cflags="-march=sapphirerapids -mtune=sapphirerapids -unroll"
      - cxxflags="-march=sapphirerapids -mtune=sapphirerapids -unroll"

    access-cice:
      require:
      - '@CICE6.6.1-0'
      - io_type=PIO
      - fflags="-march=sapphirerapids -mtune=sapphirerapids -unroll"
      - cflags="-march=sapphirerapids -mtune=sapphirerapids -unroll"
      - cxxflags="-march=sapphirerapids -mtune=sapphirerapids -unroll"

    access-mom6:
      require:
      - '@2025.07.000'
      - fflags="-march=sapphirerapids -mtune=sapphirerapids -unroll"
      - cflags="-march=sapphirerapids -mtune=sapphirerapids -unroll"
      - cxxflags="-march=sapphirerapids -mtune=sapphirerapids -unroll"

    # ... (other pinned deps: esmf, parallelio, netcdf, fms, openmpi, etc.)

    all:
      require:
      - '%oneapi@2025.2.0'
      - target=x86_64_v4

  develop:
    access-cice:
      spec: access-cice@CICE6.6.1-0
      path: /home/581/da1339/AFIM/src/access-cice
```

**Important lesson:** I initially tried adding a second `develop:` entry for `cice6@6.6.1` pointing at the same repo path, which triggered a Spack concretizer internal error (version weight uniqueness / “must choose a single version”). The working configuration is: **develop `access-cice` only**.

---

## 3) Register my dev repo with Spack (`spack develop`)

```bash
spack -e om3_cice6_dev develop --path ~/AFIM/src/access-cice access-cice@CICE6.6.1-0
```

---

## 4) Confirm Spack is selecting my dev `access-cice` (dev_path shows up in the spec)

```bash
spack -e om3_cice6_dev spec -I access-om3 | grep -n "access-cice"
```

Expected to see:

* `^access-cice@CICE6.6.1-0 ... dev_path=/home/581/da1339/AFIM/src/access-cice ... io_type=PIO ...`

That `dev_path=.../AFIM/src/access-cice` is the “proof” the concretized DAG is using my development source.

---

## 5) Build/install everything (including my dev `access-cice`)

```bash
spack -e om3_cice6_dev install --fail-fast -j 16
```

### Compile fixes applied during the build

I hit coupled-build compile errors from file versions in my repo that were missing symbols expected by the coupled configuration:

* `ice_forcing.F90`: `isleap` missing from `use ice_calendar, only: ...`
* `ice_init.F90`: `hmix_0` (and related) missing / not typed / `broadcast_scalar` mismatch

Quick fix to unblock the build: copy known-good versions from my standalone dev tree:

```bash
cp ~/AFIM/src/CICE_free-slip/cicecore/cicedyn/general/ice_init.F90 \
   ~/AFIM/src/access-cice/cicecore/cicedyn/general/

cp ~/AFIM/src/CICE_free-slip/cicecore/cicedyn/general/ice_forcing.F90 \
   ~/AFIM/src/access-cice/cicecore/cicedyn/general/

spack -e om3_cice6_dev install --fail-fast -j 16
```

After this, `access-cice` built successfully and the environment proceeded to build the remaining components.

---

## 6) Verify installed prefixes + confirm the exact build products

```bash
spack -e om3_cice6_dev find -p access-om3 access3 access-cice access-mom6
```

Installed packages in the environment:

* `access-cice@CICE6.6.1-0`
* `access-mom6@2025.07.000`
* `access3@2025.08.000`
* `access-om3@git.2025.08.001=2025.08.001`

Prefixes are under:

```bash
/g/data/gv90/da1339/spack/0.22/release/linux-rocky8-x86_64_v4/oneapi-2025.2.0/...
```

---

## 7) Locate the coupled executable I will run under payu

Once `access-om3` is installed, the coupled executable is typically in the `access-om3` prefix `bin/`:

```bash
# show where the access-om3 install lives
spack -e om3_cice6_dev find -p access-om3

# list bin dir and identify coupled exe(s)
ls -lah /g/data/gv90/da1339/spack/0.22/release/linux-rocky8-x86_64_v4/oneapi-2025.2.0/<access-om3-prefix>/bin
```

---

## 8) Architecture note for running

Because the environment is compiled with:

* `target=x86_64_v4`
* `-march=sapphirerapids -mtune=sapphirerapids`

…the payu run must land on the Sapphire Rapids queue/partition (e.g., `normalsr`) to avoid illegal-instruction failures.
