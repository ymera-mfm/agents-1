// components/AgentNetwork3D.jsx
import React, { useRef, useState, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Text, Float, Sparkles } from '@react-three/drei';
import * as THREE from 'three';

const AgentNode = ({ agent, position, onClick, isSelected }) => {
  const meshRef = useRef();
  const [hovered, setHovered] = useState(false);

  useFrame((state) => {
    if (!meshRef.current) {
      return;
    }

    // Floating animation
    meshRef.current.position.y =
      position[1] + Math.sin(state.clock.elapsedTime * 2 + agent.id) * 0.1;
    meshRef.current.rotation.y += 0.01;

    // Selection animation
    if (isSelected) {
      meshRef.current.scale.lerp(new THREE.Vector3(1.3, 1.3, 1.3), 0.1);
    } else {
      meshRef.current.scale.lerp(new THREE.Vector3(1, 1, 1), 0.1);
    }
  });

  const getAgentGeometry = (type) => {
    switch (type) {
      case 'data':
        return <octahedronGeometry args={[0.8, 0]} />;
      case 'dev':
        return <boxGeometry args={[1.2, 1.2, 1.2]} />;
      case 'cloud':
        return <sphereGeometry args={[0.9, 32, 32]} />;
      default:
        return <dodecahedronGeometry args={[0.8, 0]} />;
    }
  };

  return (
    <Float speed={2} rotationIntensity={1} floatIntensity={1}>
      <group position={position}>
        <mesh
          ref={meshRef}
          onClick={(e) => {
            e.stopPropagation();
            onClick(agent);
          }}
          onPointerOver={() => setHovered(true)}
          onPointerOut={() => setHovered(false)}
        >
          {getAgentGeometry(agent.type)}
          <meshPhysicalMaterial
            color={agent.color}
            emissive={agent.color}
            emissiveIntensity={hovered ? 0.8 : 0.3}
            transparent
            opacity={0.9}
            roughness={0.2}
            metalness={0.7}
            clearcoat={1}
            clearcoatRoughness={0.1}
          />
        </mesh>

        {/* Status particles */}
        {agent.status === 'working' && (
          <Sparkles count={10} scale={2} size={2} speed={0.3} color={agent.color} />
        )}

        {/* Agent label */}
        <Text
          position={[0, 1.5, 0]}
          fontSize={0.3}
          color="white"
          anchorX="center"
          anchorY="middle"
          maxWidth={2}
          font="/fonts/Inter-Bold.woff"
        >
          {agent.name}
        </Text>

        {/* Efficiency indicator */}
        <mesh position={[0, -1, 0]}>
          <ringGeometry args={[0.4, 0.5, 32]} />
          <meshBasicMaterial
            color={agent.color}
            transparent
            opacity={0.6}
            side={THREE.DoubleSide}
          />
        </mesh>
      </group>
    </Float>
  );
};

const ConnectionLine = ({ start, end, color, strength: _strength = 1 }) => {
  const lineRef = useRef();

  const points = useMemo(
    () => [new THREE.Vector3(...start), new THREE.Vector3(...end)],
    [start, end]
  );

  useFrame((state) => {
    if (lineRef.current) {
      // Pulsing animation for active connections
      const intensity = (Math.sin(state.clock.elapsedTime * 2) + 1) * 0.5;
      lineRef.current.material.opacity = 0.3 + intensity * 0.4;
    }
  });

  return (
    <line ref={lineRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={points.length}
          array={new Float32Array(points.flatMap((p) => [p.x, p.y, p.z]))}
          itemSize={3}
        />
      </bufferGeometry>
      <lineBasicMaterial color={color} transparent opacity={0.3} />
    </line>
  );
};

export const AgentNetwork3D = ({ agents, selectedAgent, onAgentSelect }) => {
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const calculateOrbitalPositions = (count, radius = 4) => {
    return agents.map((_, index) => {
      const angle = (index / count) * Math.PI * 2;
      const height = Math.sin(angle * 3) * 1.5;
      return [Math.cos(angle) * radius, height, Math.sin(angle) * radius];
    });
  };

  const positions = useMemo(
    () => calculateOrbitalPositions(agents.length),
    [agents.length, calculateOrbitalPositions]
  );

  return (
    <div className="w-full h-[600px] rounded-xl bg-gradient-to-br from-gray-900/50 to-black/70 border border-white/10">
      <Canvas
        camera={{ position: [0, 0, 10], fov: 50 }}
        gl={{
          antialias: true,
          alpha: true,
          powerPreference: 'high-performance',
        }}
        dpr={[1, 2]}
      >
        <color attach="background" args={['#0a0a0a']} />

        {/* Advanced Lighting */}
        <ambientLight intensity={0.4} />
        <pointLight position={[10, 10, 10]} intensity={1.5} color="#00f5ff" />
        <pointLight position={[-10, -10, -10]} intensity={0.5} color="#ff3366" />
        <spotLight position={[0, 15, 0]} angle={0.3} penumbra={1} intensity={0.8} castShadow />

        {/* Central Core */}
        <mesh>
          <sphereGeometry args={[1.5, 32, 32]} />
          <meshPhysicalMaterial
            color="#00f5ff"
            emissive="#00f5ff"
            emissiveIntensity={0.3}
            transparent
            opacity={0.2}
            roughness={0.1}
            metalness={0.9}
          />
        </mesh>

        {/* Agent Nodes */}
        {agents.map((agent, index) => (
          <React.Fragment key={agent.id}>
            <AgentNode
              agent={agent}
              position={positions[index]}
              onClick={onAgentSelect}
              isSelected={selectedAgent?.id === agent.id}
            />
            <ConnectionLine
              start={[0, 0, 0]}
              end={positions[index]}
              color={agent.color}
              strength={agent.efficiency / 100}
            />
          </React.Fragment>
        ))}

        {/* Interactive Controls */}
        <OrbitControls
          enablePan={true}
          enableZoom={true}
          enableRotate={true}
          minDistance={3}
          maxDistance={20}
          autoRotate={!selectedAgent}
          autoRotateSpeed={0.5}
        />
      </Canvas>
    </div>
  );
};
