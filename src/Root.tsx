import React from 'react';
import { Composition } from 'remotion';
import { BoneConduction } from './BoneConduction';

// ── CHUNK DEFINITIONS ─────────────────────────────────────────────
// Total: 2700 frames @ 60fps = 45 seconds
// 6 chunks, each ~7.5 seconds. Fast-paced but understandable.
//
// Chunk 1: HOOK        (0   → 220)  3.6s  – grab attention
// Chunk 2: SETUP       (180 → 540)  6.0s  – two pathways
// Chunk 3: MECHANISM   (500 → 1240) ~12s  – inside the skull
// Chunk 4: PROOF       (1200→ 1800) 10s   – oscilloscope
// Chunk 5: TWIST       (1760→ 2360) 10s   – Beethoven
// Chunk 6: OUTRO       (2320→ 2700) 6.3s  – CTA
//
// Each chunk has 20-frame overlap for seamless concat.

export const CHUNKS = [
  { id: 'chunk_01_hook',      from:    0, durationInFrames: 220 },
  { id: 'chunk_02_setup',     from:  180, durationInFrames: 360 },
  { id: 'chunk_03_mechanism', from:  500, durationInFrames: 740 },
  { id: 'chunk_04_proof',     from: 1200, durationInFrames: 600 },
  { id: 'chunk_05_twist',     from: 1760, durationInFrames: 600 },
  { id: 'chunk_06_outro',     from: 2320, durationInFrames: 380 },
] as const;

export const RemotionRoot: React.FC = () => (
  <>
    {/* Full composition */}
    <Composition
      id="BoneConduction"
      component={BoneConduction}
      durationInFrames={2700}
      fps={60}
      width={1080}
      height={1920}
    />
    {/* Individual chunk compositions */}
    {CHUNKS.map(chunk => (
      <Composition
        key={chunk.id}
        id={chunk.id}
        component={BoneConduction}
        durationInFrames={chunk.durationInFrames}
        fps={60}
        width={1080}
        height={1920}
        defaultProps={{}}
      />
    ))}
  </>
);
