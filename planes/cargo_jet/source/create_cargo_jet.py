"""Run: blender --background --python planes/cargo_jet/source/create_cargo_jet.py"""

import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'shared'))
from aircraft import Aircraft


a = Aircraft(__file__, 'cargo_jet', 52.0)
body = [(-25, .12, .17, 1.65), (-22, .8, .65, 1.35),
        (-17, 2.25, 1.85, .55), (-12, 3.05, 2.95, 0), (10, 3.05, 2.95, 0),
        (15, 2.75, 2.75, -.02), (18, 2.1, 2.18, -.15),
        (20.4, 1.2, 1.35, -.45), (22, .35, .48, -.72), (22.5, .03, .06, -.8)]
a.loft('Fuselage', body, a.paint, segments=48)
a.loft('Nose radome', [(20.4, 1.215, 1.365, -.45), (22, .365, .495, -.72),
                       (22.515, .032, .062, -.8)], a.teal, segments=48)
for side, sign in [('right', 1), ('left', -1)]:
    def mirror(points):
        return [(x, sign*y, z) for x, y, z in points]

    for i, (back, front) in enumerate([(14.6, 16), (16.16, 17.6), (17.76, 19.3)]):
        a.skin(f'Cockpit window_{side}_{i+1}', body, [back, front],
               [.38 + j*.08 for j in range(7)], sign, a.glass, .04)
    a.skin('Fuselage stripe_' + side, body, [-16, 13.5], [-.06, .02, .1], sign, a.teal, .04)
    # Bulged landing-gear sponsons and an upswept ramp distinguish the freight body.
    a.loft('Gear sponson_' + side, [(-10, .1, .15, -1.55), (-7, .85, .9, -1.7),
           (3, .95, 1, -1.65), (6, .1, .15, -1.5)], a.paint, sign*2.7)
    a.slab('High wing_' + side, mirror([
        (4.8, 2.2, 1.8), (-4.7, 26, 1.1), (-6.75, 26, 1.1),
        (-6.25, 13, 1.48), (-4.1, 2.2, 1.8),
    ]), .40, a.paint)
    a.slab('Winglet_' + side, mirror([
        (-4.65, 25.9, 1.1), (-5.8, 25.9, 3.4),
        (-6.7, 25.9, 3.4), (-6.75, 25.9, 1.1),
    ]), .20, a.teal, axis='Y')
    a.slab('Winglet cap_' + side, mirror([
        (-5.55, 25.89, 2.9), (-5.8, 25.89, 3.42),
        (-6.7, 25.89, 3.42), (-6.71, 25.89, 2.9),
    ]), .22, a.orange, axis='Y')
    a.slab('Flap marking_' + side, mirror([
        (-3.55, 4, 1.956), (-5.22, 12, 1.72),
        (-6.02, 12, 1.72), (-4.44, 4, 1.956),
    ]), .015, a.teal)
    a.slab('Aileron marking_' + side, mirror([
        (-5.65, 16, 1.6), (-6.05, 24.8, 1.34),
        (-6.69, 24.8, 1.34), (-6.36, 16, 1.6),
    ]), .015, a.teal)
    for engine, x, y in [('inner', 2.2, 8.2), ('outer', -1.7, 16)]:
        z = -.6
        wing_z = 1.8 - (y - 2.2) * .7 / 23.8
        a.slab(f'Engine pylon_{side}_{engine}', mirror([
            (x+.6, y, .35), (x+.1, y, wing_z),
            (x-2.5, y, wing_z), (x-2.5, y, .35),
        ]), .35, a.teal, axis='Y')
        a.engine(f'{side}_{engine}', x, sign*y, z, 1.35)
    a.slab('T-tail horizontal stabilizer_' + side, mirror([
        (-18.2, .06, 9), (-21.5, 9.3, 9.3), (-24, 9.3, 9.3), (-23.2, .06, 9),
    ]), .3, a.paint)
    a.slab('Elevator marking_' + side, mirror([
        (-22.7, 2, 9.22), (-23.25, 8.8, 9.44),
        (-23.94, 8.8, 9.44), (-23.36, 2, 9.22),
    ]), .015, a.teal)
a.slab('Vertical stabilizer', [(-13.7, 0, 1.6), (-18.2, 0, 9),
                              (-23.2, 0, 9), (-24, 0, 1.65)], .4, a.teal, axis='Y')
a.slab('Rudder marking', [(-21.65, 0, 2.8), (-21.3, 0, 8.3),
                         (-23.25, 0, 8.3), (-23.85, 0, 2.8)], .42, a.orange, axis='Y')
a.slab('Closed rear cargo ramp', [(-12.5, -1.7, -2.88), (-12.5, 1.7, -2.88),
                                (-21.3, .65, .35), (-21.3, -.65, .35)], .13, a.teal)
a.finish(rear=True)
