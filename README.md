# ml_planes assets

Blender source files and exported visual assets for the airframes defined in the
`ml_planes` simulator live in this repository. Aerodynamic configuration,
controller tuning, and simulation code remain in `ml_planes`.

No aircraft assets have been created yet. [PLANES.md](PLANES.md) is the inventory and
tracks the asset required for each currently shipped plane configuration.

## Layout

```text
planes/
  <plane-id>/
    source/       Blender working files (`.blend`)
    textures/     Textures specific to this plane
    exports/      Runtime-ready exports such as `.glb`
shared/
  materials/      Reusable material resources
  textures/       Textures shared by multiple planes
```

Plane IDs match the filename stem used by `ml_planes/assets/planes/*.plane.ron`. Keeping
those names aligned makes it possible to associate a simulation configuration with its
visual asset without a second naming scheme.

Blender recovery and autosave files are ignored. Before committing large binary source,
texture, or export files, this project should adopt an agreed binary-storage policy such
as Git LFS.
