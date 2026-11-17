// اختبار سريع لمكونات Cinematic المحسنة
import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import {CameraRig} from './camera';
import {NoiseShapesLayer, SceneTransitionEffect} from './transitions';
import {MapOverlay} from './fx';
import {MotionCtx, useTheme} from './theme';

export const CinematicTest: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  
  return (
    <AbsoluteFill>
      {/* Vignette + overlay for cinematic depth */}
      <MapOverlay opacity={0.85} />
      
      {/* Dynamic background shapes */}
      <NoiseShapesLayer seed={42} />
      
      {/* Camera movement test */}
      <CameraRig mode="push-in" shakeFrame={30} shakeIntensity={0.5}>
        <div style={{
          position: 'absolute',
          top: 400,
          left: 80,
          right: 80,
          padding: '40px 60px',
          background: 'rgba(11, 18, 32, 0.85)',
          borderRadius: 24,
          border: '2px solid #D4AF37',
          boxShadow: '0 20px 50px rgba(0,0,0,0.5)',
          backdropFilter: 'blur(12px)',
        }}>
          <h2 style={{
            fontFamily: 'Cairo, sans-serif',
            fontSize: 48,
            fontWeight: 900,
            color: '#D4AF37',
            textAlign: 'center',
            direction: 'rtl',
          }}>
            اختبار الجودة السينمائية
          </h2>
          <p style={{
            fontFamily: 'Cairo, sans-serif',
            fontSize: 28,
            color: '#ffffff',
            textAlign: 'center',
            direction: 'rtl',
            marginTop: 16,
          }}>
            حركة الكاميرا: push-in | الإضاءة: ديناميكية | التدرج: فيجنيت
          </p>
        </div>
      </CameraRig>
      
      {/* Caption area with scrim */}
      <div style={{
        position: 'absolute',
        bottom: 300,
        left: 80,
        right: 80,
        padding: '20px 40px',
        background: 'linear-gradient(to bottom, transparent, rgba(0,0,0,0.7))',
        borderRadius: 16,
      }}>
        <p style={{
          fontFamily: 'Cairo, sans-serif',
          fontSize: 32,
          color: '#ffffff',
          textAlign: 'center',
          direction: 'rtl',
        }}>
          هذا المشهد يختبر التحسينات السينمائية
        </p>
      </div>
    </AbsoluteFill>
  );
};

export const TransitionCinematographyTest: React.FC<{transition: any, idx: number}> = ({transition, idx}) => {
  return (
    <SceneTransitionEffect
      transition={transition}
      index={idx}
      enableSfx={true}
    />
  );
};
