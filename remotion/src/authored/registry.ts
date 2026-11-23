/**
 * Registry of authored scenes (written by the art director, see pipeline/scene_author.py).
 * Scene files are copied from the job folder (outputs/<job>/scenes/) into this directory right before every
 * preview / render, so what you preview is what gets rendered. webpack's require.context picks them up; this file
 * never changes. The copied *.tsx files are git-ignored.
 */
import type React from 'react';
import type {SceneProps} from '../kit';

declare const require: any;

const ctx = require.context('./', false, /^\.\/(?!registry).*\.tsx$/);

export const AUTHORED: Record<string, React.FC<SceneProps>> = Object.fromEntries(
  ctx.keys().map((k: string) => [k.replace(/^\.\//, '').replace(/\.tsx$/, ''), ctx(k).default]),
);
