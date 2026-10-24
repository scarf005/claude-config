---
name: game-critic
description: Review a game level, encounter or screen the way a professional game critic and level designer would, from real captured frames, then drive fix-and-recapture rounds until no serious issue remains. Use for requests to critique, polish or "make it perfect" for aesthetics, game feel, pacing, encounter staging, readability or immersion of a game stage.
---

# Game critic

Judge from what the player sees, never from code alone. Code explains a problem; only a captured frame or a played
second proves it exists or is gone.

## Method

1. State the fantasy: what the player should feel in this stretch (the repository's goal doc, if any) and the one
   verb they perform most. Every finding is judged against it.
2. Gather evidence through the production path: autoplay or capture tools at the moments that matter (first sight of
   each encounter, the second after it starts, mid-fight, the release after it, section transitions, bosses). At least
   one frame per beat; also a top-down or map view for layout. Look at each frame at full size.
3. Write findings as: severity, what the player sees (frame path), why it hurts the fantasy, the smallest fix.
   Severity: S1 breaks immersion or fairness or the core verb; S2 clearly weakens a beat; S3 polish.
4. Fix S1 and S2 yourself, recapture the same moments, and re-judge. Repeat. Stop only when a fresh full pass finds
   no S1 or S2; list the remaining S3 and every unverified path.
5. Never end a round with "not measured" items you could measure now. Turn each lens into a number first (spawn
   distance, enemy count and spacing, course time, reachable area, floor under the body everywhere) and sweep it
   exhaustively; a lens checked only where a bug was already reported is unchecked.

## Lenses (check all, in this order)

- **Reveal and staging**: threats must enter from a believable place (horizon, behind a landmark, through haze or a
  doorway), never pop into open space within the player's attention. Time to read the threat, then to act, then to
  be hit: a telegraph the player can see before it matters.
- **Distance and scale**: engagement range should suit the weapon and screen size. Too close removes dodging and
  aiming; too far makes targets sub-readable. Check apparent size in pixels at the range the fight really happens.
- **Pacing**: a tension curve, not a flat line. Build, peak, release; a quiet stretch must exist and be earned; the
  peak must be the loudest, densest and best-composed moment. Compare section lengths and enemy counts.
- **Composition and readability**: foreground, midground, background layers; value contrast so enemies and pickups
  separate from terrain; silhouettes distinct per enemy role; a landmark or leading line that tells the player where
  to look; no large flat, empty, same-coloured areas on screen for long.
- **Place and identity**: each section looks and sounds different, has one memorable landmark, and tells part of the
  setting's story. The map is a place, not a corridor with props.
- **Verticality and terrain**: height variation, cover, elevation changes, occlusion that creates choices.
- **Game feel**: hit feedback, impacts, camera response, audio cues; the player's power reads on screen.
- **Traversal and collision**: the player can go everywhere the picture says they can, and nowhere it says they
  cannot. Hunt invisible walls, auto-steering, snagging and dead zones by sweeping the controlled body across the
  whole playable width at many positions (not by reading code) and comparing where it stops with what is drawn
  there. Every block must be a visible object; a rule that moves the player without the player's input is an S1.
  Sweep height too: place the body at every reachable lateral and distance position (edges, section boundaries,
  arena corners) and assert it neither sinks nor tilts off the drawn floor; floor extents must cover every sample the
  body takes, not only its centre.
- **Threat uptime**: every enemy must actually threaten. With the player moving at real speed and not killing it, log
  each enemy kind's shots per ten seconds from arrival to death and the seconds from start to first contact; a
  hunter that stays alive but fires less than once per ten seconds, or stalls in a state loop (reposition, cover,
  band edge), is an S1. Station keeping must hold while the target moves, not only against a stationary player.
- **Fairness**: deaths are explainable from the frame; damage sources are visible; no off-screen or through-wall
  hits; recovery resources arrive when the curve needs them.
- **Consistency**: style, palette and detail density match across sections; no placeholder-looking areas.

## Rules

- Do not praise to fill space; report only what changes decisions. Name what you did not look at.
- A passing test is not evidence for a visual or feel claim; a capture at the reported moment is.
- Fixes must keep the design contract of the project (core fantasy, performance budget); if a fix trades one
  against the other, say so.
- Compare before and after captures of the same moment and save them under the project's screenshot folder.

## Grounding (researched 2026-10-09)

- Trace every complaint from the felt aesthetic (tension, fantasy, sensation) back to the dynamic and then the rule
  that causes it (MDA, Hunicke/LeBlanc/Zubek 2004: https://users.cs.northwestern.edu/~hunicke/MDA.pdf); fix the rule,
  not the symptom.
- Far enemies make the environment matter, because range lets terrain and cover shape the fight (Mike Stout, GDC 2012,
  cited at https://book.leveldesignbook.com/process/combat/enemy). Reveal at range, engage at a stated hold distance.
- Never let an enemy attack the instant it appears or hit from off-screen; shape formations to demand a response,
  alternate firefights with quiet stretches, and keep effects (beams, lingering smoke) from hiding threats
  (https://redharegames.wordpress.com/2026/07/15/simple-article-how-to-design-rail-shooters-for-players-today/).
- Each enemy role needs its own silhouette readable at mid-range and a telegraph of state and intent
  (https://book.leveldesignbook.com/process/combat/enemy, https://www.gamedeveloper.com/design/enemy-attacks-and-telegraphing).
- Use level patterns on purpose: elevated enemy positions and galleries raise tension and restrict the player's
  movement; choke points expose whoever passes; give the player an occasional position of advantage to lower
  tension (Hullett and Whitehead, Design Patterns in FPS Levels: https://users.soe.ucsc.edu/~ejw/papers/hullett-fps-fdg2010.pdf).
- Landmarks at composition intersections guide the eye and identify areas; similar silhouettes flatten a map
  (https://book.leveldesignbook.com/process/env-art).
