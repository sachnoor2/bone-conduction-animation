import React from 'react';
import { Composition } from 'remotion';
import { LizardTail } from './LizardTail';

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
    <Composition
      id="LizardTail"
      component={LizardTail}
      durationInFrames={2700}
      fps={60}
      width={1080}
      height={1920}
    />
    {CHUNKS.map(chunk => (
      <Composition
        key={chunk.id}
        id={chunk.id}
        component={LizardTail}
        durationInFrames={chunk.durationInFrames}
        fps={60}
        width={1080}
        height={1920}
        defaultProps={{}}
      />
    ))}
  </>
);
