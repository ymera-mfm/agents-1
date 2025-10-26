// components/ParticleEffects.jsx
import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

export const DataFlowParticles = ({ count = 1000, speed = 0.5, color = '#00f5ff' }) => {
  const points = useRef();
  const particlesPosition = useMemo(() => {
    const positions = new Float32Array(count * 3);

    for (let i = 0; i < count; i++) {
      const i3 = i * 3;
      // Create spiral distribution
      const radius = Math.random() * 10;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);

      positions[i3] = radius * Math.sin(phi) * Math.cos(theta);
      positions[i3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
      positions[i3 + 2] = radius * Math.cos(phi);
    }

    return positions;
  }, [count]);

  useFrame((state) => {
    if (!points.current) {
      return;
    }

    const positions = points.current.geometry.attributes.position.array;
    const time = state.clock.getElapsedTime();

    for (let i = 0; i < count; i++) {
      const i3 = i * 3;

      // Animate particles in flowing motion
      positions[i3] += Math.sin(time + positions[i3]) * 0.01 * speed;
      positions[i3 + 1] += Math.cos(time + positions[i3 + 1]) * 0.008 * speed;
      positions[i3 + 2] += Math.sin(time + positions[i3 + 2]) * 0.012 * speed;

      // Reset particles that move too far
      if (Math.abs(positions[i3]) > 15) {
        positions[i3] = 0;
      }
      if (Math.abs(positions[i3 + 1]) > 15) {
        positions[i3 + 1] = 0;
      }
      if (Math.abs(positions[i3 + 2]) > 15) {
        positions[i3 + 2] = 0;
      }
    }

    points.current.geometry.attributes.position.needsUpdate = true;
  });

  return (
    <points ref={points}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={particlesPosition.length / 3}
          array={particlesPosition}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.05}
        color={color}
        transparent
        opacity={0.8}
        blending={THREE.AdditiveBlending}
        sizeAttenuation={true}
      />
    </points>
  );
};

export const AgentConnectionBeams = ({ agents, connections }) => {
  const linesRef = useRef();

  const lineGeometry = useMemo(() => {
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(connections.length * 6); // 2 points per connection

    connections.forEach((connection, index) => {
      const startAgent = agents.find((a) => a.id === connection.from);
      const endAgent = agents.find((a) => a.id === connection.to);

      if (startAgent && endAgent) {
        const i6 = index * 6;
        positions[i6] = startAgent.position.x;
        positions[i6 + 1] = startAgent.position.y;
        positions[i6 + 2] = startAgent.position.z;
        positions[i6 + 3] = endAgent.position.x;
        positions[i6 + 4] = endAgent.position.y;
        positions[i6 + 5] = endAgent.position.z;
      }
    });

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    return geometry;
  }, [agents, connections]);

  useFrame((state) => {
    if (!linesRef.current) {
      return;
    }

    // Pulsing animation for active connections
    const intensity = (Math.sin(state.clock.getElapsedTime() * 2) + 1) * 0.5;
    linesRef.current.material.opacity = 0.2 + intensity * 0.3;
  });

  return (
    <lineSegments ref={linesRef} geometry={lineGeometry}>
      <lineBasicMaterial color="#00f5ff" transparent opacity={0.3} linewidth={1} />
    </lineSegments>
  );
};
