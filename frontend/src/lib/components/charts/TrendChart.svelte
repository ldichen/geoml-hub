<script>
	/**
	 * TrendChart.svelte - 仿 HuggingFace 风格的趋势图组件
	 *
	 * Props:
	 * - data: Array<{date: string, value: number}> - 趋势数据
	 * - color: string - 曲线和渐变颜色 (默认 '#3b82f6')
	 * - height: number - 图表高度 (默认 50)
	 * - width: number - 图表宽度 (默认 200)
	 */
	export let data = [];
	export let color = '#3b82f6';
	export let height = 50;
	export let width = 200;

	let hoveredPoint = null;
	let tooltipX = 0;
	let tooltipY = 0;

	$: processedData = processData(data);
	$: pathD = generatePath(processedData);
	$: areaD = generateArea(processedData);

	/**
	 * 处理数据：计算坐标和缩放
	 */
	function processData(rawData) {
		if (!rawData || rawData.length === 0) {
			return [];
		}

		const values = rawData.map(d => d.value);
		const maxValue = Math.max(...values, 1); // 至少为1，避免除零
		const minValue = Math.min(...values, 0);
		const range = maxValue - minValue || 1;

		const padding = 2;
		const chartWidth = width - padding * 2;
		const chartHeight = height - padding * 2;

		return rawData.map((d, i) => {
			const x = padding + (i / (rawData.length - 1 || 1)) * chartWidth;
			const normalizedValue = (d.value - minValue) / range;
			const y = padding + chartHeight - normalizedValue * chartHeight;

			return {
				x,
				y,
				originalValue: d.value,
				date: d.date
			};
		});
	}

	/**
	 * 生成平滑贝塞尔曲线路径
	 */
	function generatePath(points) {
		if (points.length === 0) return '';
		if (points.length === 1) return `M ${points[0].x} ${points[0].y}`;

		let path = `M ${points[0].x} ${points[0].y}`;

		for (let i = 0; i < points.length - 1; i++) {
			const current = points[i];
			const next = points[i + 1];

			// 计算控制点以创建平滑曲线
			const controlPointX = current.x + (next.x - current.x) / 2;

			path += ` Q ${controlPointX} ${current.y}, ${next.x} ${next.y}`;
		}

		return path;
	}

	/**
	 * 生成填充区域路径（曲线 + 底边）
	 */
	function generateArea(points) {
		if (points.length === 0) return '';

		const linePath = generatePath(points);
		const lastPoint = points[points.length - 1];
		const firstPoint = points[0];

		// 添加垂直线到底部，然后水平线回到起点，最后垂直线回到起始点
		return `${linePath} L ${lastPoint.x} ${height} L ${firstPoint.x} ${height} Z`;
	}

	/**
	 * 处理鼠标移动事件
	 */
	function handleMouseMove(event) {
		const svg = event.currentTarget;
		const rect = svg.getBoundingClientRect();
		const mouseX = event.clientX - rect.left;

		// 找到最接近的数据点
		const closest = processedData.reduce((prev, curr) => {
			return Math.abs(curr.x - mouseX) < Math.abs(prev.x - mouseX) ? curr : prev;
		});

		hoveredPoint = closest;
		tooltipX = closest.x;
		tooltipY = closest.y - 10;
	}

	/**
	 * 处理鼠标离开事件
	 */
	function handleMouseLeave() {
		hoveredPoint = null;
	}

	/**
	 * 格式化日期显示
	 */
	function formatDate(dateStr) {
		const date = new Date(dateStr);
		return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
	}

	/**
	 * 格式化数值显示
	 */
	function formatValue(value) {
		if (value >= 1000) {
			return (value / 1000).toFixed(1) + 'k';
		}
		return value.toString();
	}
</script>

<div class="trend-chart-container">
	<svg
		{width}
		{height}
		class="trend-chart"
		on:mousemove={handleMouseMove}
		on:mouseleave={handleMouseLeave}
	>
		<!-- 渐变定义 -->
		<defs>
			<linearGradient id="gradient-{color}" x1="0%" y1="0%" x2="0%" y2="100%">
				<stop offset="0%" style="stop-color:{color};stop-opacity:0.3" />
				<stop offset="100%" style="stop-color:{color};stop-opacity:0.05" />
			</linearGradient>
		</defs>

		<!-- 填充区域 -->
		{#if areaD}
			<path
				d={areaD}
				fill="url(#gradient-{color})"
				class="trend-area"
			/>
		{/if}

		<!-- 曲线 -->
		{#if pathD}
			<path
				d={pathD}
				stroke={color}
				stroke-width="2"
				fill="none"
				class="trend-line"
			/>
		{/if}

		<!-- 悬停点 -->
		{#if hoveredPoint}
			<circle
				cx={hoveredPoint.x}
				cy={hoveredPoint.y}
				r="4"
				fill={color}
				class="hover-point"
			/>
		{/if}
	</svg>

	<!-- Tooltip -->
	{#if hoveredPoint}
		<div
			class="tooltip"
			style="left: {tooltipX}px; top: {tooltipY}px;"
		>
			<div class="tooltip-date">{formatDate(hoveredPoint.date)}</div>
			<div class="tooltip-value">{formatValue(hoveredPoint.originalValue)}</div>
		</div>
	{/if}
</div>

<style>
	.trend-chart-container {
		position: relative;
		display: inline-block;
	}

	.trend-chart {
		display: block;
		cursor: crosshair;
	}

	.trend-line {
		stroke-linecap: round;
		stroke-linejoin: round;
	}

	.trend-area {
		pointer-events: none;
	}

	.hover-point {
		filter: drop-shadow(0 0 4px rgba(0, 0, 0, 0.2));
	}

	.tooltip {
		position: absolute;
		background: rgba(0, 0, 0, 0.85);
		color: white;
		padding: 6px 10px;
		border-radius: 6px;
		font-size: 12px;
		pointer-events: none;
		white-space: nowrap;
		transform: translate(-50%, -100%);
		z-index: 10;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
	}

	.tooltip-date {
		font-weight: 500;
		margin-bottom: 2px;
	}

	.tooltip-value {
		font-size: 14px;
		font-weight: 600;
	}
</style>
