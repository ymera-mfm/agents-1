import React, { useRef, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Text, Float } from '@react-three/drei';
import * as THREE from 'three';

const AgentNode = ({ agent, position, onClick }) => {
  const meshRef = useRef();
  const [hovered, setHovered] = useState(false);

  useFrame((state) => {
    if (meshRef.current) {
      // Gentle floating animation
      meshRef.current.rotation.y += 0.01;
      meshRef.current.position.y = position[1] + Math.sin(state.clock.elapsedTime + agent.id) * 0.1;
    }
  });

  const getAgentShape = (type) => {
    switch (type) {
      case 'data':
        return <octahedronGeometry args={[1, 0]} />;
      case 'dev':
        return <boxGeometry args={[1.5, 1.5, 1.5]} />;
      case 'cloud':
        return <sphereGeometry args={[1, 16, 16]} />;
      default:
        return <sphereGeometry args={[1, 32, 32]} />;
    }
  };

  return (
    <Float speed={2} rotationIntensity={1} floatIntensity={1}>
      <mesh
        ref={meshRef}
        position={position}
        onClick={onClick}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
        scale={hovered ? 1.2 : 1}
      >
        {getAgentShape(agent.type)}
        <meshPhysicalMaterial
          color={agent.color}
          emissive={agent.color}
          emissiveIntensity={agent.status === 'working' ? 0.5 : 0.2}
          transparent
          opacity={0.9}
          roughness={0.2}
          metalness={0.8}
        />
      </mesh>

      {/* Agent label */}
      <Text
        position={[position[0], position[1] + 2, position[2]]}
        fontSize={0.5}
        color="white"
        anchorX="center"
        anchorY="middle"
      >
        {agent.name}
      </Text>

      {/* Status indicator */}
      <mesh position={[position[0] + 1.2, position[1], position[2]]}>
        <sphereGeometry args={[0.2, 8, 8]} />
        <meshBasicMaterial
          color={
            agent.status === 'working'
              ? '#00ff00'
              : agent.status === 'thinking'
                ? '#ffff00'
                : '#666666'
          }
        />
      </mesh>
    </Float>
  );
};

const ConnectionLine = ({ start, end, color }) => {
  const lineRef = useRef();

  const points = [start, end].map((point) => new THREE.Vector3(...point));

  return (
    <line ref={lineRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={points.length}
          array={new Float32Array(points.flat())}
          itemSize={3}
        />
      </bufferGeometry>
      <lineBasicMaterial color={color} transparent opacity={0.6} />
    </line>
  );
};

export const Agent3DVisualization = ({ agents, onAgentSelect }) => {
  const calculatePositions = (count, radius = 5) => {
    return agents.map((_, index) => {
      const angle = (index / count) * Math.PI * 2;
      return [Math.cos(angle) * radius, Math.sin(angle) * radius * 0.3, Math.sin(angle) * radius];
    });
  };

  const positions = calculatePositions(agents.length);

  return (
    <div className="w-full h-96 rounded-lg bg-black/20">
      <Canvas camera={{ position: [0, 0, 10], fov: 50 }} gl={{ antialias: true, alpha: true }}>
        <color attach="background" args={['#0a0a0a']} />

        {/* Lighting */}
        <ambientLight intensity={0.4} />
        <pointLight position={[10, 10, 10]} intensity={1} />
        <spotLight position={[-10, -10, -10]} angle={0.3} penumbra={1} intensity={0.5} />

        {/* Central hub */}
        <mesh>
          <sphereGeometry args={[2, 32, 32]} />
          <meshPhysicalMaterial
            color="#00f5ff"
            emissive="#00f5ff"
            emissiveIntensity={0.2}
            transparent
            opacity={0.3}
          />
        </mesh>

        {/* Agent nodes */}
        {agents.map((agent, index) => (
          <React.Fragment key={agent.id}>
            <AgentNode
              agent={agent}
              position={positions[index]}
              onClick={() => onAgentSelect(agent)}
            />
            <ConnectionLine start={[0, 0, 0]} end={positions[index]} color={agent.color} />
          </React.Fragment>
        ))}

        <OrbitControls
          enablePan={true}
          enableZoom={true}
          enableRotate={true}
          minDistance={5}
          maxDistance={20}
        />
      </Canvas>
    </div>
  );
};
