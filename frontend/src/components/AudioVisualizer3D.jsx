// components/AudioVisualizer3D.jsx
import React, { useRef, useEffect, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

export const AudioVisualizer3D = ({ audioContext, audioSource }) => {
  const [analyser, setAnalyser] = useState(null);
  const [frequencyData, setFrequencyData] = useState(null);
  const barsRef = useRef();

  useEffect(() => {
    if (!audioContext || !audioSource) {
      return;
    }

    const analyserNode = audioContext.createAnalyser();
    analyserNode.fftSize = 256;
    audioSource.connect(analyserNode);

    const dataArray = new Uint8Array(analyserNode.frequencyBinCount);
    setAnalyser(analyserNode);
    setFrequencyData(dataArray);

    return () => {
      analyserNode.disconnect();
    };
  }, [audioContext, audioSource]);

  useFrame(() => {
    if (!analyser || !frequencyData || !barsRef.current) {
      return;
    }

    analyser.getByteFrequencyData(frequencyData);

    const bars = barsRef.current.children;
    for (let i = 0; i < bars.length; i++) {
      const bar = bars[i];
      const frequencyValue = frequencyData[i] / 255;

      // Animate bar scale based on frequency
      bar.scale.y = 0.1 + frequencyValue * 2;
      bar.position.y = bar.scale.y / 2;

      // Color based on frequency intensity
      const material = bar.material;
      material.color.setHSL(frequencyValue * 0.3, 1, 0.5);
      material.emissive.setHSL(frequencyValue * 0.3, 1, frequencyValue * 0.3);
    }
  });

  return (
    <group ref={barsRef}>
      {Array.from({ length: 32 }).map((_, i) => (
        <mesh key={i} position={[i - 16, 0, 0]}>
          <boxGeometry args={[0.8, 0.1, 0.8]} />
          <meshStandardMaterial
            color={new THREE.Color().setHSL(i / 32, 1, 0.5)}
            emissive={new THREE.Color().setHSL(i / 32, 1, 0.2)}
          />
        </mesh>
      ))}
    </group>
  );
};
