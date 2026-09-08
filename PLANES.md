# Plane asset inventory

This inventory was derived from the five `*.plane.ron` configurations currently shipped
in `ml_planes/assets/planes/`. Each row represents one distinct visual asset that still
needs to be made.

| Status | Plane ID | Visual brief | Simulation reference | Asset workspace |
| --- | --- | --- | --- | --- |
| Planned | `business_jet` | Light business jet in the Embraer Phenom 300 / Citation CJ class; 16 m span | `ml_planes/assets/planes/business_jet.plane.ron` | `planes/business_jet/` |
| Planned | `cargo_jet` | Heavy four-engine military airlifter in the C-17 class; 52 m span | `ml_planes/assets/planes/cargo_jet.plane.ron` | `planes/cargo_jet/` |
| Planned | `electric_trainer` | Small battery-electric trainer or demonstrator; 8 m span | `ml_planes/assets/planes/electric_trainer.plane.ron` | `planes/electric_trainer/` |
| Planned | `generic_jet` | Generic jet placeholder airframe; 10 m span | `ml_planes/assets/planes/generic_jet.plane.ron` | `planes/generic_jet/` |
| Planned | `tanker` | Four-engine aerial-refueling tanker in the KC-135R class; 40 m span | `ml_planes/assets/planes/tanker.plane.ron` | `planes/tanker/` |

The class descriptions and spans come from the corresponding simulation configurations.
They establish broad silhouette and scale targets; they do not require exact replicas of
the named real-world aircraft. The simulator currently draws planes as gizmos and has no
committed mesh-loading contract, so export orientation, origin, node names, materials, and
level-of-detail requirements remain to be specified before modeling begins.
