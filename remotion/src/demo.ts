import type {Spec} from './types';
import {demoStyle} from './demoStyle';
import {demoScenesA} from './demoScenesA';
import {demoScenesB} from './demoScenesB';
export const demoSpec: Spec = {
  "fps": 30,
  "width": 1080,
  "height": 1920,
  "total": 1170,
  "audio": "audio.wav",
  "style": demoStyle,
  "scenes": [...demoScenesA, ...demoScenesB],
} as unknown as Spec;
