"""Run: blender --background --python planes/electric_trainer/source/create_electric_trainer.py"""

import math
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'shared'))
from aircraft import Aircraft


a = Aircraft(__file__, 'electric_trainer', 8.0)
a.loft('Fuselage', [(-3.7, .035, .06, .1), (-3, .2, .25, .04),
       (-1.4, .43, .49, 0), (.5, .57, .59, 0), (1.5, .48, .46, -.03),
       (2.35, .29, .29, -.1), (2.65, .23, .23, -.1)], a.paint)
a.loft('Cockpit canopy', [(-1.1, .07, .08, .48), (-.6, .42, .35, .58),
       (.45, .50, .47, .61), (1.15, .34, .37, .52), (1.65, .05, .055, .37)], a.glass)
for side, sign in [('right', 1), ('left', -1)]:
    def mirror(points):
        return [(x, sign*y, z) for x, y, z in points]

    a.slab('Straight wing_' + side, mirror([
        (.8, .35, -.25), (.65, 3.65, -.02), (.46, 4, .005),
        (-.65, 4, .005), (-.91, 3.65, -.02), (-1.02, .35, -.25),
    ]), .13, a.paint)
    a.slab('Wingtip_' + side, mirror([
        (.65, 3.65, .049), (.46, 4, .074), (-.65, 4, .074), (-.91, 3.65, .049),
    ]), .01, a.orange)
    a.slab('Aileron marking_' + side, mirror([
        (-.65, 2.1, -.055), (-.67, 3.6, .05),
        (-.9, 3.6, .05), (-.95, 2.1, -.055),
    ]), .01, a.teal)
    a.slab('Horizontal stabilizer_' + side, mirror([
        (-2.47, .12, .1), (-2.9, 1.5, .16), (-3.65, 1.5, .16), (-3.55, .12, .1),
    ]), .09, a.teal)
    # Flush side access cover suggests the electric powerplant without fake intakes.
    a.slab('Motor access panel_' + side, mirror([
        (1.72, .411, -.15), (2.12, .325, -.15),
        (2.12, .325, .02), (1.72, .411, .02),
    ]), .012, a.teal, axis='Y')
a.slab('Vertical stabilizer', [(-2.1, 0, .3), (-2.7, 0, 1.7),
                              (-3.3, 0, 1.7), (-3.65, 0, .1)], .13, a.teal, axis='Y')
a.slab('Fin cap', [(-2.59, 0, 1.45), (-2.7, 0, 1.71),
                  (-3.3, 0, 1.71), (-3.355, 0, 1.45)], .14, a.orange, axis='Y')
a.loft('Electric motor cowling', [(2.26, .315, .315, -.1), (2.66, .25, .25, -.1)], a.teal)
a.loft('Propeller spinner', [(2.67, .23, .23, -.1), (2.88, .18, .18, -.1),
                            (3.13, .012, .012, -.1)], a.paint)
for blade in range(3):
    angle = blade * math.tau / 3 + .15
    def blade_points(outline):
        return [(2.72, r*math.cos(angle)-w*math.sin(angle),
                 -.1+r*math.sin(angle)+w*math.cos(angle)) for r, w in outline]
    a.slab(f'Propeller blade_{blade+1}', blade_points([
        (.14, -.06), (.5, -.13), (1.05, -.04), (1.12, .08), (.94, .16), (.24, .09),
    ]), .045, a.dark, axis='X')
    a.slab(f'Propeller tip_{blade+1}', blade_points([
        (.94, -.059), (1.05, -.04), (1.12, .08), (.94, .16),
    ]), .05, a.orange, axis='X')
a.finish()
