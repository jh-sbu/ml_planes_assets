"""Run: blender --background --python planes/business_jet/source/create_business_jet.py"""

import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'shared'))
from aircraft import Aircraft


a = Aircraft(__file__, 'business_jet', 16.0)
body = [(-7.5, .06, .08, .15), (-6.6, .32, .36, .1),
        (-4.8, .68, .72, 0), (-3, .9, .95, 0), (3.2, .9, .95, 0),
        (4.5, .75, .78, -.03), (5.5, .5, .5, -.15),
        (6.5, .18, .20, -.27), (6.9, .015, .025, -.3)]
a.loft('Fuselage', body, a.paint, segments=48)
a.loft('Nose radome', [(6.1, .31, .33, -.222), (6.5, .19, .21, -.27),
                       (6.91, .016, .026, -.3)], a.teal, segments=48)
for side, sign in [('right', 1), ('left', -1)]:
    def mirror(points):
        return [(x, sign*y, z) for x, y, z in points]

    for i, (back, front) in enumerate([(3.7, 4.45), (4.55, 5.35)]):
        a.skin(f'Cockpit window_{side}_{i+1}', body, [back, front],
               [.3 + j*.09 for j in range(7)], sign, a.glass)
    for i in range(6):
        x = -2.8 + i*.88
        a.skin(f'Cabin window_{side}_{i+1}', body, [x, x+.40],
               [.22 + j*.06 for j in range(6)], sign, a.glass, .012)
    a.skin('Fuselage stripe_' + side, body, [-5.4, 5.35], [-.09, -.02, .05], sign, a.teal)
    a.slab('Wing_' + side, mirror([
        (1.35, .6, -.48), (-1.8, 8, .12), (-2.55, 8, .12), (-2.35, .6, -.48),
    ]), .16, a.paint)
    a.slab('Aileron marking_' + side, mirror([
        (-2.13, 4.8, -.05), (-2.28, 7.65, .18),
        (-2.52, 7.65, .18), (-2.43, 4.8, -.05),
    ]), .01, a.teal)
    a.slab('Winglet_' + side, mirror([
        (-1.73, 7.94, .12), (-2.12, 7.94, 1.22),
        (-2.48, 7.94, 1.22), (-2.55, 7.94, .12),
    ]), .12, a.teal, axis='Y')
    a.slab('Winglet cap_' + side, mirror([
        (-2.045, 7.93, 1), (-2.12, 7.93, 1.23),
        (-2.48, 7.93, 1.23), (-2.494, 7.93, 1),
    ]), .14, a.orange, axis='Y')
    a.slab('Engine mount_' + side, mirror([
        (-3.1, .55, .27), (-3.5, 1.55, .37), (-4.85, 1.55, .37), (-4.65, .55, .27),
    ]), .16, a.teal)
    a.engine(side, -3.9, sign*1.52, .48, .53)
    a.slab('T-tail horizontal stabilizer_' + side, mirror([
        (-5.48, .04, 2.95), (-6.45, 2.75, 3.06),
        (-7.2, 2.75, 3.06), (-6.94, .04, 2.95),
    ]), .12, a.paint)
a.slab('Vertical stabilizer', [(-4.4, 0, .54), (-5.5, 0, 2.96),
                              (-6.94, 0, 2.96), (-7.2, 0, .25)], .18, a.teal, axis='Y')
a.slab('Rudder marking', [(-6.4, 0, .72), (-6.35, 0, 2.65),
                         (-6.97, 0, 2.65), (-7.14, 0, .72)], .19, a.orange, axis='Y')
a.finish()
