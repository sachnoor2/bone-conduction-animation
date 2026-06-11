import React from 'react';
import { Composition } from 'remotion';
import { BoneConduction } from './BoneConduction';

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="BoneConduction"
      component={BoneConduction}
      durationInFrames={2700}
      fps={60}
      width={1080}
      height={1920}
    />
  </>
);