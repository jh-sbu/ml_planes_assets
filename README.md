# ml_planes assets

Blender source files and exported visual assets for the airframes defined in the
`ml_planes` simulator live in this repository. Aerodynamic configuration,
controller tuning, and simulation code remain in `ml_planes`.

All five airframes have basic Blender models, GLB exports, and rendered previews:
[business jet](planes/business_jet/README.md), [cargo jet](planes/cargo_jet/README.md),
[electric trainer](planes/electric_trainer/README.md),
[generic jet](planes/generic_jet/README.md), and [tanker](planes/tanker/README.md).
[PLANES.md](PLANES.md) tracks the assets for each currently
shipped plane configuration.

## Layout

```text
planes/
  <plane-id>/
    source/       Blender working files (`.blend`)
    textures/     Textures specific to this plane
    exports/      Runtime-ready exports such as `.glb`
shared/
  aircraft.py      Blender mesh, material, export, and studio helpers for new models
  materials/      Reusable material resources
  textures/       Textures shared by multiple planes
```

Plane IDs match the filename stem used by `ml_planes/assets/planes/*.plane.ron`. Keeping
those names aligned makes it possible to associate a simulation configuration with its
visual asset without a second naming scheme.

Each plane README includes its Blender Python rebuild command. The business jet,
cargo jet, and electric trainer generators import `shared/aircraft.py`; keep the
repository layout intact when rebuilding. Only Blender's bundled Python API is needed.
After rebuilding, run `just sync-models` in the sibling `ml_planes` checkout to refresh
the runtime copies. All five simulator configurations reference their respective GLBs.

Verify the saved sources and re-import every GLB with:

```sh
blender --background --python-exit-code 1 --python shared/validate_assets.py
```

This checks dimensions, mesh and triangle counts, origins, export axes, and that
the GLBs contain embedded materials and aircraft geometry without the preview studio.
On headless Linux systems without an audio server, prefix Blender commands with
`ALSOFT_DRIVERS=null` to avoid audio initialization and shutdown hangs.

Blender recovery and autosave files are ignored. Before committing large binary source,
texture, or export files, this project should adopt an agreed binary-storage policy such
as Git LFS.
