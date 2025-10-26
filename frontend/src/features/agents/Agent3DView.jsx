import React, { useEffect, useRef, memo } from 'react';

export const Agent3DView = memo(({ agents }) => {
  const canvasRef = useRef(null);
  const rotationRef = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) {
      return;
    }
    const ctx = canvas.getContext('2d');
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;

    let frame;
    const render = () => {
      ctx.fillStyle = 'rgba(10, 10, 10, 0.1)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      rotationRef.current += 0.01;

      agents.forEach((agent, i) => {
        const angle = (i / agents.length) * Math.PI * 2 + rotationRef.current;
        const radius = 80;
        const x = centerX + Math.cos(angle) * radius;
        const y = centerY + Math.sin(angle) * radius;
        const size = 20 + Math.sin(rotationRef.current * 2 + i) * 5;

        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.lineTo(x, y);
        ctx.strokeStyle = `${agent.color}40`;
        ctx.lineWidth = 2;
        ctx.stroke();

        const gradient = ctx.createRadialGradient(x, y, 0, x, y, size);
        gradient.addColorStop(0, agent.color);
        gradient.addColorStop(1, `${agent.color}00`);

        ctx.beginPath();
        ctx.arc(x, y, size, 0, Math.PI * 2);
        ctx.fillStyle = gradient;
        ctx.fill();

        if (agent.status === 'working') {
          const pulseSize = size + Math.sin(rotationRef.current * 5) * 8;
          ctx.beginPath();
          ctx.arc(x, y, pulseSize, 0, Math.PI * 2);
          ctx.strokeStyle = `${agent.color}80`;
          ctx.lineWidth = 2;
          ctx.stroke();
        }

        ctx.fillStyle = '#fff';
        ctx.font = '12px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(agent.name, x, y + size + 15);
      });

      const hubGradient = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, 30);
      hubGradient.addColorStop(0, '#00f5ff');
      hubGradient.addColorStop(1, '#00f5ff00');
      ctx.beginPath();
      ctx.arc(centerX, centerY, 30, 0, Math.PI * 2);
      ctx.fillStyle = hubGradient;
      ctx.fill();

      frame = requestAnimationFrame(render);
    };
    render();

    return () => cancelAnimationFrame(frame);
  }, [agents]);

  return <canvas ref={canvasRef} width={400} height={400} className="w-full h-full" />;
});
