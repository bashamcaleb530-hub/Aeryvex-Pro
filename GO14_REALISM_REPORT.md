# Go 14 — Animation realism

## Implemented
- Smoothed gait blending for starts/stops; locomotion phase slows while standing.
- Split standing breathing from restrained two-step movement bounce.
- Better step-cycle knee flex, foot counter-rotation retained.
- Head counter-rotation and lateral stabilization when body twists.
- Delayed cape reaction to movement, still a geometry proxy (not cloth physics).

## Limitations
These are procedural pivot animations, not motion-captured or skinned skeletal animation. No video evaluation, Godot runtime verification, or physical foot-ground contact solving was performed. Existing movement speed interface unchanged. Realism assessment remains at 18% pending visual and engine verification; no automatic advancement.
