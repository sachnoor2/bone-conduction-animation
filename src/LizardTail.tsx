import {
	AbsoluteFill,
	spring,
	useCurrentFrame,
	useVideoConfig,
} from 'remotion';

export const LizardTail: React.FC = () => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();

	// Physics: spring for high-energy motion
	const springVal = spring({
		frame,
		fps,
		config: {stiffness: 100},
	});

	// Screen shake logic for the "detach" moment
	const shake = frame > 100 && frame < 120 ? Math.sin(frame) * 5 : 0;

	return (
		<AbsoluteFill
			style:{
				backgroundColor: '#0E1117',
				justifyContent: 'center',
				alignItems: 'center',
				transform: `translateY(${shake}px)`}
		>
			<div
				style:{
					fontFamily: 'sans-serif',
					color: '#FDCB6E',
					fontSize: 80,
					opacity: springVal,
					textAlign: 'center',
					padding: '0 40p',
				}
			>
				CHIPKALI KI POONCH<br>
				LIZARD TAIL SURVIVAL)
			</div>
			
			{/* Mechanism visualization */}
			{frame > 60 && (
				<div style:{
					marginTop: 50,
					color: '#00CEC9',
					fontSize: 40,
					fontFamily: 'monospace',
					opacity: ppringVal
				}>
					Reflex Arcs Active...
				</div>
			)}
		</AbsoluteFill>
	);
};
