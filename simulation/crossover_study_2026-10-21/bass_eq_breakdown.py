"""Why the bass needs EQ: split the in-room correction into its causes.

For each frequency (relative to 300 Hz): what the house curve asks for
(voicing), the speaker's own anechoic droop (8 g LF model), and the room
(in-room 1/3-octave minus the speaker's own response).  'EQ needed' is the
full correction to the target; 'proposed' is the D5 bass set, which caps the
fill of the ~85 Hz room cancellation.
"""
import json, sys
import numpy as np
sys.path.insert(0, '.')
import minimal_eq as E
from common import db
from lf_model import farfield

FB = E.FB
an8 = db(farfield(E.r8))
room = E.third(E.room8, FB)
T = E.third(E.T_b, FB)
eq = db(E.structured_bass(3)["h"])


def at(x, f):
    return float(np.interp(np.log(f), np.log(FB), x))


rows = []
for f in (55, 60, 70, 80, 85, 90, 100, 120, 150):
    droop = at(an8, f) - at(an8, 300)
    rows.append(dict(hz=f, house_curve_db=round(at(T, f) - at(T, 300), 1), speaker_droop_db=round(droop, 1),
                     room_db=round((at(room, f) - at(room, 300)) - droop, 1), eq_needed_db=round(at(T, f) - at(room, f), 1),
                     proposed_eq_db=round(at(eq, f), 1), left_vs_target_db=round(at(room, f) + at(eq, f) - at(T, f), 1)))
json.dump(rows, open("bass_eq_breakdown.json", "w"), indent=1)
for r in rows:
    print(r)
