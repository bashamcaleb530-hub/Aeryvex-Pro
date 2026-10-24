# Go 8: Allied and enemy infantry squads

## Added
- Three allied and three enemy AI-controlled infantry proxies in Fronts only.
- Soldiers prioritize nearby enemy soldiers, otherwise travel toward command posts their team does not own.
- Solders contribute to post capture or contesting; defeated soldiers respawn after 5 seconds and deduct one ticket.
- Basic ranged damage simulation with cooldowns, unit counts displayed on HUD.
- Soldier instances are removed on mode changes and match resets.

## Checks
- Python source and regression tests run; test results passed.
- Full Godot runtime execution, FPS benchmarks, pathfinding around obstacles, visuals, and balancing are NOT verified.
- This is six simple proxy AI soldiers, not finished Battlefront-scale combat; soldiers currently fight each other and do not damage the hero fighters.
