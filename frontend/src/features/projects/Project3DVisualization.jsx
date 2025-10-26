import React, { useEffect, useRef, memo } from 'react';
import * as THREE from 'three';

export const Project3DVisualization = memo(({ project }) => {
  const mountRef = useRef(null);
  const meshesRef = useRef([]);
  const animationRef = useRef(null);

  useEffect(() => {
    if (!mountRef.current) {
      return;
    }

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, mountRef.current.clientWidth / 400, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });

    renderer.setSize(mountRef.current.clientWidth, 400);
    renderer.setClearColor(0x000000, 0);
    mountRef.current.appendChild(renderer.domElement);

    camera.position.z = 8;
    camera.position.y = 2;

    const ambientLight = new THREE.AmbientLight(0x404040, 2);
    scene.add(ambientLight);

    const pointLight = new THREE.PointLight(0x00f5ff, 2, 50);
    pointLight.position.set(5, 5, 5);
    scene.add(pointLight);

    const phases = project.phases || [];
    const spacing = 3;
    const startX = (-(phases.length - 1) * spacing) / 2;

    phases.forEach((phase, index) => {
      let geometry;
      switch (phase.geometry) {
        case 'octahedron':
          geometry = new THREE.OctahedronGeometry(0.5);
          break;
        case 'torus':
          geometry = new THREE.TorusGeometry(0.4, 0.15, 16, 100);
          break;
        case 'dodecahedron':
          geometry = new THREE.DodecahedronGeometry(0.5);
          break;
        case 'tetrahedron':
          geometry = new THREE.TetrahedronGeometry(0.6);
          break;
        default:
          geometry = new THREE.SphereGeometry(0.5, 32, 32);
      }

      const material = new THREE.MeshPhongMaterial({
        color: phase.color,
        emissive: phase.color,
        emissiveIntensity: phase.status === 'in_progress' ? 0.5 : 0.2,
        transparent: true,
        opacity: 0.9,
      });

      const mesh = new THREE.Mesh(geometry, material);
      mesh.position.x = startX + index * spacing;
      mesh.userData = { phase, index };
      scene.add(mesh);
      meshesRef.current.push(mesh);

      if (index < phases.length - 1) {
        const points = [
          new THREE.Vector3(mesh.position.x, 0, 0),
          new THREE.Vector3(startX + (index + 1) * spacing, 0, 0),
        ];
        const lineGeometry = new THREE.BufferGeometry().setFromPoints(points);
        const line = new THREE.Line(lineGeometry, new THREE.LineBasicMaterial({ color: 0x374151 }));
        scene.add(line);
      }
    });

    let frame = 0;

    const animate = () => {
      animationRef.current = requestAnimationFrame(animate);
      frame += 0.01;

      meshesRef.current.forEach((mesh, index) => {
        mesh.rotation.y += 0.01;
        mesh.rotation.x += 0.005;
        mesh.position.y = Math.sin(frame + index) * 0.3;

        if (mesh.userData.phase.status === 'in_progress') {
          const pulse = Math.sin(frame * 3) * 0.15 + 1;
          mesh.scale.setScalar(pulse);
        }
      });

      camera.position.x = Math.sin(frame * 0.3) * 2;
      camera.lookAt(0, 0, 0);
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      // Store ref values for cleanup to avoid stale closure
      // eslint-disable-next-line react-hooks/exhaustive-deps
      const meshes = meshesRef.current;
      // eslint-disable-next-line react-hooks/exhaustive-deps
      const mount = mountRef.current;
      meshes.forEach((mesh) => {
        mesh.geometry.dispose();
        mesh.material.dispose();
      });
      if (mount && renderer.domElement) {
        mount.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, [project]);

  return <div ref={mountRef} className="w-full h-96 rounded-xl" />;
});
