---
name: game-critic
description: Review a game level, encounter or screen the way a professional game critic and level designer would, from real captured frames, then drive fix-and-recapture rounds until no serious issue remains. Use for requests to critique, polish or "make it perfect" for aesthetics, game feel, pacing, encounter staging, readability or immersion of a game stage.
---
# Game critic

Judge from what the player sees, never from code alone. Only a captured frame or a played second proves a problem
exists or is gone.

## Method

1. State the fantasy (the repository's goal doc, if any) and the one verb the player performs most. Judge against it.
2. Gather frames through the production path: first sight of each encounter, the second after it starts, mid-fight,
   the release after it, section transitions, bosses; one frame per beat plus a top-down view. View at full size.
3. Findings: severity, what the player sees (frame path), why it hurts the fantasy, smallest fix. S1 breaks immersion,
   fairness or the core verb; S2 clearly weakens a beat; S3 polish.
4. Fix S1 and S2 yourself, recapture the same moments, re-judge. Stop when a fresh full pass finds none; list the
   remaining S3 and every unverified path.
5. Never end a round with "not measured" items you could measure now. Turn each lens into a number (spawn distance,
   enemy count and spacing, course time, reachable area, floor under the body) and sweep it exhaustively; a lens
   checked only where a bug was already reported is unchecked.

## Lenses (check all, in order)

- Reveal and staging: threats enter from a believable place (horizon, landmark, haze, doorway), never pop into open
  space; time to read, act, be hit; a visible telegraph.
- Distance and scale: range suits weapon and screen; check apparent pixel size at the real fight range.
- Pacing: build, peak, release; an earned quiet stretch; the peak is the loudest, densest moment. Compare section
  lengths and enemy counts.
- Composition and readability: three depth layers; value contrast separates enemies and pickups from terrain; distinct
  silhouette per role; a landmark or leading line; no long flat same-coloured areas.
- Place and identity: each section looks and sounds different, has one landmark, tells part of the story.
- Verticality and terrain: height variation, cover, elevation changes, occlusion that creates choices.
- Game feel: hit feedback, impacts, camera response, audio cues; player power reads on screen.
- Traversal and collision: sweep the body across the whole playable width at many positions (not by reading code) and
  compare stops with what is drawn; every block is a visible object; a rule that moves the player without input is
  S1. Sweep height too: at edges, section boundaries and arena corners the body neither sinks nor tilts off the floor;
  floor extents cover every sample the body takes, not only its centre.
- Threat uptime: with the player moving at real speed, log each enemy kind's shots per ten seconds and seconds to first
  contact; a hunter firing under once per ten seconds, or stuck in a state loop (reposition, cover, band edge), is
  S1. Station keeping must hold while the target moves.
- Fairness: deaths explainable from the frame; damage sources visible; no off-screen or through-wall hits; recovery
  resources arrive when the curve needs them.
- Consistency: style, palette, detail density match across sections; no placeholder-looking areas.

## Rules

- No filler praise; report only what changes decisions. Name what you did not look at.
- A passing test is no evidence for a visual or feel claim; a capture at the reported moment is.
- Fixes keep the project's design contract (core fantasy, performance budget); say so if a fix trades one for the other.
- Save before and after captures of the same moment under the project's screenshot folder.

## Grounding

- Trace complaints from felt aesthetic to dynamic to rule; fix the rule (MDA: https://users.cs.northwestern.edu/~hunicke/MDA.pdf).
- Reveal at range, engage at a stated hold distance; range lets terrain matter (https://book.leveldesignbook.com/process/combat/enemy).
- No attack the instant an enemy appears or from off-screen; alternate firefights with quiet stretches; effects must
  not hide threats (https://redharegames.wordpress.com/2026/07/15/simple-article-how-to-design-rail-shooters-for-players-today/).
- Each role needs a mid-range silhouette and a telegraph (https://www.gamedeveloper.com/design/enemy-attacks-and-telegraphing).
- Level patterns: galleries raise tension, choke points expose, advantage positions lower it (https://users.soe.ucsc.edu/~ejw/papers/hullett-fps-fdg2010.pdf).
- Landmarks guide the eye; similar silhouettes flatten a map (https://book.leveldesignbook.com/process/env-art).
