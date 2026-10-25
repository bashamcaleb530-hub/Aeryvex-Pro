# Aeryvex Pro — Living Galaxies Exploration and War Design v1

## Player promise
Ten explorable galaxies, not ten menu arenas. Every galaxy gets a social hub, accessible interiors, faction governance, repeatable player-driven missions, training spaces, terrain exploration, a warfront and a capital. The core loop connects on-foot exploration, aerial traversal, portal transport, warfare, politics and succession.

## Travel rule: flight + portals
- **Celestial Arches** remain the principal intergalactic and interplanetary transport network. No requirement to pilot spacecraft between stars.
- **Lightning Flight**: energy-equipped high-level warriors can glide and then fly across planetary landscapes by shaping lightning fields. Flight costs current energy and permits aerial scouting, dodging and combat.
- **Regional flyers**: purchasable or rideable original gliders, flying fauna and hover platforms for non-elite characters. Flying supports meaningful navigation and exploration without undermining portals.
- Army movement uses **War Gates**; defending or losing one changes strategic mobility, supply and access.
- Distances inside a planet are intentional: walkable cities, flyable exterior regions, portal-connected districts.

## Ten galaxies: each has a distinct playable place and identity
| Galaxy | Ruler | Exploration signature | Key interiors | Mission types |
| --- | --- | --- | --- | --- |
| Aurelia | Orion Valen | layered capital spires, sanctuaries | Prism Council hall, academy, archive, shops, family apartments | council votes, training, royal defense, petitions |
| Velithra | Maeryn Sol | floating bridges and ocean cities | gate control rooms, workshops, tide homes | rescue, portal calibration, evacuation, siege defense |
| Ormath | Thalen Orris | mountain ramparts and army camps | barracks, war college, command bunker | field drill, lead assault, protect stronghold |
| Eidara | Ilyra Venn | vertical city, secret underground paths | spy bureaus, embassies, data-vaults | scouting, infiltration, discover informants, evidence |
| Cyravelle | Selene Avaris | living forests and healing terraces | infirmaries, conservatories, council annex | search/rescue, defend settlement, civilian aid |
| Nexavar | Drakthar Vex | crimson gate capital, black glass towers | sovereign court, inheritance shrine, tribunal | espionage, lord duel, infiltrate court |
| Kharvoss | Malveris Thorne | factory ridges, fortress highways | forge halls, worker tenements, arms depots | sabotage, free workers, disable gate defenses |
| Veyscar | Nyssara Veil | rainlit markets, bridges and estate roofs | noble mansions, shadow brokers, safe houses | stealth, secrets, social deception |
| Urakhen | Korr Uldane | volcanic canyons and raider plains | arena, war tents, lava foundry | survival, capture banners, duel commanders |
| Mournreach | Vaelith Sorn | crystal burial cities, hollow caverns | inheritance vault, echo chapel, archive | mysteries, succession interruption, ancient relic discovery |

## Accessible interiors
Main campaign buildings must be enterable: council chamber, barracks, training yard, academy classrooms, archive, infirmary, armory, market, workshops, throne chambers, governor halls and homes related to quests. Provide meaningful interaction, not empty doors: conversations, clues, merchants, training, investigations, construction, petitions, votes. Major hubs have ambient NPC routines and schedules; interiors can stream in separate Godot scenes.

## Gameplay systems
1. **Training yards**: basic attacks, straight/curved/branching electricity, parry, dodge, aerial combat, staff and hand-casting, sparring against rank-appropriate opponents; tutorials unlock skills through actual use.
2. **Councils and governing**: five Aether Grand Masters, Purple Master generals, war votes, petitions, succession nominations; regional rulers issue orders, can be challenged by political choices, vote histories persist.
3. **Scout and spy**: scout forest and rooftops, discover portal routes, obtain gate codes, tail informants, plant decoys, extract files, disrupt communications; intelligence has mechanical impact on later battle strength.
4. **Planet defense**: alarms, civilian evacuation, reinforce a gate, hold city lanes, repel an invasion, protect commanders; saved towns rebuild and remember the player.
5. **Destruction and sabotage**: target enemy war infrastructure (fictional depots and power conduits), disable foundries and gates, destroy weapons stockpiles; visible physical destruction and long-term economic effects.
6. **Conquest and reconstruction**: sieges, commander duels, occupation policy, mercy or retaliation, rebuild neighborhoods, choose governors, manage unrest.
7. **Flight and exploration**: unlock gliding, then flight; vertical traversal, aerial enemy patrols, hidden ruins, caves, elevated buildings and optional landmarks.
8. **Inheritance outcomes**: duels yield defeated, killed-with-transfer or essence-destroyed; rank-based essence nullification; successor takes the relevant current unless prevented. Five Grand Masters can use Rainbow Ascension, five Void Grand Lords can use Crimson Cataclysm.
9. **Relationships and dynasties**: trust, betrayal, promises, companions, political marriages only where character ages and consent are appropriate; non-romance relationships equally important.
10. **War simulation**: portal control, supplies, local loyalties, garrisons, faction influence and troop readiness inform what happens after leaving an area.

## Sellable scope: playable vertical slice before ten-galaxy expansion
**First deliverable: Aurelia capital + nearby Kharvoss invasion zone**
- Third-person movement + camera; enter **three** purposeful buildings: training yard, council hall, infirmary.
- One aerial traversal area; one Celestial Arch to enemy perimeter.
- Sparring drill demonstrating blue and purple lightning, hand-casting and a staff demo.
- Council meeting with two consequential vote choices.
- Scout enemy gate; spy to steal defense data or fight to trigger stronger defense.
- Defend a civilian district; two possible moral decisions.
- Fight a Void commander; victory updates faction state, town damage and successor data.
- Exit to hub, see civilian aftermath, faction reputation and map changes.
- Controller/mouse keyboard support, readable quest markers, accessibility, save/load, scalable settings and stable frame times.

### Beyond the slice
World streaming scenes, progression, voiced or text dialogue, local NPC routines, weather, shops, high-fidelity art and polished combat. Each new galaxy must introduce a unique traversal, culture, environment, combat problem and political dilemma; avoid copy-paste content.

## Validation
Before calling a feature finished: run in-engine tests plus actual in-game manual testing. For 3D character approval verify front, side, and rear renders, correct textured mesh, rig, animation and scene integration. Gameplay prototype source is not proof the complete content exists.

## Commercial distinction
Use wholly original art, architecture, language, rank symbols, music, outfits and characters. Never simply substitute names for recognizable third-party fictional assets. Names and branding need clearance ahead of distribution.
