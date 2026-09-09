# Plane asset inventory

This inventory was derived from the five `*.plane.ron` configurations currently shipped
in `ml_planes/assets/planes/`. Each row represents one distinct visual asset.

| Status | Plane ID | Visual brief | Simulation reference | Asset workspace |
| --- | --- | --- | --- | --- |
| Basic model complete | `business_jet` | Light business jet in the Embraer Phenom 300 / Citation CJ class; 16 m span | `ml_planes/assets/planes/business_jet.plane.ron` | [Model and export](planes/business_jet/README.md) |
| Basic model complete | `cargo_jet` | Heavy four-engine military airlifter in the C-17 class; 52 m span | `ml_planes/assets/planes/cargo_jet.plane.ron` | [Model and export](planes/cargo_jet/README.md) |
| Basic model complete | `electric_trainer` | Small battery-electric trainer or demonstrator; 8 m span | `ml_planes/assets/planes/electric_trainer.plane.ron` | [Model and export](planes/electric_trainer/README.md) |
| Basic model complete | `generic_jet` | Generic jet placeholder airframe; 10 m span | `ml_planes/assets/planes/generic_jet.plane.ron` | [Model and export](planes/generic_jet/README.md) |
| Basic model complete | `tanker` | Four-engine aerial-refueling tanker in the KC-135R class; 40 m span | `ml_planes/assets/planes/tanker.plane.ron` | [Model and export](planes/tanker/README.md) |

The class descriptions and spans come from the corresponding simulation configurations.
They establish broad silhouette and scale targets; they do not require exact replicas of
the named real-world aircraft. All five configurations now reference their GLB through
the simulator's `visual` block with `BlenderYUp` orientation and scale 1.0. Models use
meters and a nominal center-of-gravity origin; see each README for node names and
material conventions. Additional levels of detail, animation, and collision meshes
remain outside these basic visual assets.
