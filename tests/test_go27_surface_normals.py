"""Go 27: shoulder bridge normals must account for diagonal axes."""
from pathlib import Path
import math
src = (Path(__file__).resolve().parents[1] / 'scripts' / 'SkinnedTransitions.gd').read_text()
assert 'var axis = (after - before).normalized()' in src
assert 'var n = radial - axis * radial.dot(axis)' in src
assert 'n = n.normalized()' in src
# Analytic equivalent: perpendicular to a diagonal shoulder bridge.
axis = (0.6, -0.8, 0)
radial = (1, 0, 0)
dot = sum(a*b for a,b in zip(axis,radial))
n = tuple(r - a*dot for r,a in zip(radial,axis))
norm = math.sqrt(sum(x*x for x in n))
n = tuple(x/norm for x in n)
assert abs(sum(a*b for a,b in zip(axis,n))) < 1e-9
print('GO27_NORMALS_PASS')
