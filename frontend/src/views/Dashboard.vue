<template>
  <v-container fluid class="dashboard-wrap pa-6">
    <v-row justify="center">
      <v-col cols="12" xl="10" lg="11">
        <v-sheet class="pa-4 dashboard-shell" rounded="lg" elevation="1">
          <!-- TOP ROW -->
          <v-row class="mb-4" no-gutters>
            <!-- LEFT HEIGHT PANEL -->
            <v-col cols="12" md="2" class="pr-md-3 mb-4 mb-md-0">
              <v-sheet class="panel pa-3 d-flex flex-column align-center justify-center" rounded="0">
                <div class="tank-box">
                  <div class="tank-outline">
                    <div class="tank-fill" :style="{ height: tankFillHeight }"></div>

                    <div class="tank-marker" :style="{ bottom: tankFillHeight }">
                      <div class="tank-dot"></div>
                      <div class="tank-label">{{ liveData.waterheight }}</div>
                    </div>
                  </div>
                </div>

                <div class="tank-caption mt-3">Height({{ heightUnit }})</div>
              </v-sheet>
            </v-col>

            <!-- TOP CHART PANEL -->
            <v-col cols="12" md="10">
              <v-sheet class="panel pa-3" rounded="0">
                <div class="panel-title-row">
                  <div class="panel-title">Water Reserves(10 min)</div>
                  <div class="menu-icon">≡</div>
                </div>

                <div class="chart-area">
                  <div class="y-axis-label">Water level</div>

                  <svg viewBox="0 0 820 320" class="line-chart-svg" preserveAspectRatio="none">
                    <rect x="70" y="30" width="700" height="220" fill="white" stroke="#222" stroke-width="1.5" />

                    <text x="32" y="42" class="axis-label">{{ gaugeMax }}</text>
                    <text x="32" y="97" class="axis-label">{{ Math.round(gaugeMax * 0.75) }}</text>
                    <text x="32" y="152" class="axis-label">{{ Math.round(gaugeMax * 0.5) }}</text>
                    <text x="32" y="207" class="axis-label">{{ Math.round(gaugeMax * 0.25) }}</text>
                    <text x="52" y="252" class="axis-label">0</text>

                    <path :d="chartAreaPath" fill="#5fb7ee" stroke="none" opacity="0.95" />
                    <path :d="chartLinePath" fill="none" stroke="#3c97d3" stroke-width="3" />

                    <text
                      v-for="(label, i) in chartLabels"
                      :key="`label-${i}`"
                      :x="chartLabelX(i)"
                      y="278"
                      class="axis-label small"
                      text-anchor="middle"
                    >
                      {{ label }}
                    </text>

                    <text x="405" y="305" class="axis-label" text-anchor="middle">Time</text>
                  </svg>

                  <div class="chart-legend">
                    <span class="legend-line"></span>
                    <span>Water</span>
                  </div>
                </div>
              </v-sheet>
            </v-col>
          </v-row>

          <!-- BOTTOM ROW -->
          <v-row no-gutters>
            <!-- GAUGE PANEL -->
            <v-col cols="12" md="8" class="pr-md-3 mb-4 mb-md-0">
              <v-sheet class="panel pa-3" rounded="0">
                <div class="panel-title-row">
                  <div class="panel-title">Water Reserves</div>
                  <div class="menu-icon">≡</div>
                </div>

                <div class="gauge-wrap">
                  <svg viewBox="0 0 520 280" class="gauge-svg" preserveAspectRatio="xMidYMid meet">
                    <!-- colored arc -->
                    <path :d="buildArcPath(180, 135, gaugeRadius)" class="gauge-segment-red" />
                    <path :d="buildArcPath(135, 81, gaugeRadius)" class="gauge-segment-yellow" />
                    <path :d="buildArcPath(81, 0, gaugeRadius)" class="gauge-segment-green" />

                    <!-- ticks -->
                    <line
                      v-for="(tick, index) in gaugeTicks"
                      :key="`tick-line-${index}`"
                      :x1="tick.line.x1"
                      :y1="tick.line.y1"
                      :x2="tick.line.x2"
                      :y2="tick.line.y2"
                      class="gauge-tick-line"
                    />

                    <!-- labels -->
                    <text
                      v-for="(tick, index) in gaugeTicks"
                      :key="`tick-label-${index}`"
                      :x="tick.labelPos.x"
                      :y="tick.labelPos.y"
                      class="gauge-tick-label"
                      text-anchor="middle"
                    >
                      {{ tick.label }}
                    </text>

                    <!-- needle -->
                    <line
                      :x1="gaugeCx"
                      :y1="gaugeCy"
                      :x2="needlePoint.x"
                      :y2="needlePoint.y"
                      class="gauge-needle"
                    />
                    <circle :cx="gaugeCx" :cy="gaugeCy" r="10" class="gauge-center-dot" />

                    <!-- value under needle -->
                    <text
                      :x="gaugeCx"
                      y="252"
                      class="gauge-value-text"
                      text-anchor="middle"
                    >
                      {{ reserveDisplay }} {{ reserveUnit }}
                    </text>
                  </svg>
                </div>
              </v-sheet>
            </v-col>

            <!-- PERCENT PANEL -->
            <v-col cols="12" md="4">
              <v-sheet class="panel pa-3 percent-panel" rounded="0">
                <div class="water-level-title">Water Level</div>
                <div class="water-level-subtitle">Capacity Remaining</div>

                <div class="percent-circle-wrap">
                  <div class="percent-circle">
                    <div class="percent-inner">
                      {{ safePercentage }}%
                    </div>
                  </div>
                </div>
              </v-sheet>
            </v-col>
          </v-row>
        </v-sheet>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onBeforeUnmount } from "vue";
import { useMqttStore } from "@/store/mqttStore";

const Mqtt = useMqttStore();

const liveData = reactive({
  id: "",
  type: "",
  radar: 0,
  waterheight: 0,
  reserve: 0,
  percentage: 0,
  timestamp: 0,
});

const history = ref([]);
const heightUnit = ref("in");
const reserveUnit = ref("Gal");

// top left tank
const safePercentage = computed(() => {
  const p = Number(liveData.percentage) || 0;
  return Math.max(0, Math.min(100, Math.round(p)));
});

const tankFillHeight = computed(() => {
  return `${safePercentage.value}%`;
});

// gauge numbers
const reserveDisplay = computed(() => {
  const val = Number(liveData.reserve) || 0;
  return `${Math.round(val)}`;
});

const gaugeMax = computed(() => {
  const values = history.value.map(item => Number(item.reserve) || 0);
  const localMax = Math.max(...values, Number(liveData.reserve) || 0, 100);
  return Math.ceil(localMax / 100) * 100;
});

// SVG gauge geometry
const gaugeCx = 260;
const gaugeCy = 190;
const gaugeRadius = 145;

function pointOnGauge(angleDeg, radius) {
  const rad = (angleDeg * Math.PI) / 180;
  return {
    x: gaugeCx + radius * Math.cos(rad),
    y: gaugeCy - radius * Math.sin(rad),
  };
}

function buildArcPath(startAngle, endAngle, radius) {
  const step = startAngle > endAngle ? -3 : 3;
  let d = "";
  let first = true;

  for (
    let angle = startAngle;
    step < 0 ? angle >= endAngle : angle <= endAngle;
    angle += step
  ) {
    const p = pointOnGauge(angle, radius);
    d += first ? `M ${p.x} ${p.y}` : ` L ${p.x} ${p.y}`;
    first = false;
  }

  const end = pointOnGauge(endAngle, radius);
  d += ` L ${end.x} ${end.y}`;
  return d;
}

const needleAngle = computed(() => {
  const reserve = Number(liveData.reserve) || 0;
  const ratio = Math.max(0, Math.min(1, reserve / gaugeMax.value));
  return 180 - ratio * 180;
});

const needlePoint = computed(() => {
  return pointOnGauge(needleAngle.value, gaugeRadius - 26);
});

const gaugeTicks = computed(() => {
  const ticks = [];
  const total = 10;

  for (let i = 0; i <= total; i++) {
    const ratio = i / total;
    const angle = 180 - ratio * 180;

    const inner = pointOnGauge(angle, gaugeRadius - 10);
    const outer = pointOnGauge(angle, gaugeRadius + 8);
    const label = pointOnGauge(angle, gaugeRadius + 28);

    ticks.push({
      label: Math.round(gaugeMax.value * ratio),
      line: {
        x1: inner.x,
        y1: inner.y,
        x2: outer.x,
        y2: outer.y,
      },
      labelPos: {
        x: label.x,
        y: label.y + 5,
      },
    });
  }

  return ticks;
});

// top chart data
const chartData = computed(() => {
  const arr = history.value.slice(-10);
  if (arr.length === 0) {
    return [
      { reserve: 0, timestamp: 0 },
      { reserve: 0, timestamp: 0 },
    ];
  }
  return arr;
});

const chartLabels = computed(() => {
  return chartData.value.map(item => formatSmallTime(item.timestamp));
});

const chartLabelX = (index) => {
  const count = chartData.value.length;
  if (count <= 1) return 420;
  return 70 + (700 * index) / (count - 1);
};

const chartLinePath = computed(() => {
  const data = chartData.value;
  const plotX = 70;
  const plotY = 30;
  const plotW = 700;
  const plotH = 220;
  const maxY = gaugeMax.value || 100;

  if (data.length === 1) {
    const y = plotY + plotH - (Number(data[0].reserve || 0) / maxY) * plotH;
    return `M ${plotX} ${y} L ${plotX + plotW} ${y}`;
  }

  let d = "";
  data.forEach((item, index) => {
    const x = plotX + (plotW * index) / (data.length - 1);
    const y = plotY + plotH - (Number(item.reserve || 0) / maxY) * plotH;
    d += index === 0 ? `M ${x} ${y}` : ` L ${x} ${y}`;
  });

  return d;
});

const chartAreaPath = computed(() => {
  const data = chartData.value;
  const plotX = 70;
  const plotY = 30;
  const plotW = 700;
  const plotH = 220;
  const baseY = plotY + plotH;
  const maxY = gaugeMax.value || 100;

  if (data.length === 1) {
    const y = plotY + plotH - (Number(data[0].reserve || 0) / maxY) * plotH;
    return `M ${plotX} ${baseY} L ${plotX} ${y} L ${plotX + plotW} ${y} L ${plotX + plotW} ${baseY} Z`;
  }

  let d = `M ${plotX} ${baseY}`;

  data.forEach((item, index) => {
    const x = plotX + (plotW * index) / (data.length - 1);
    const y = plotY + plotH - (Number(item.reserve || 0) / maxY) * plotH;
    d += ` L ${x} ${y}`;
  });

  d += ` L ${plotX + plotW} ${baseY} Z`;
  return d;
});

function formatSmallTime(ts) {
  if (!ts) return "--:--:--";
  const d = new Date(Number(ts) * 1000);
  if (isNaN(d.getTime())) return "--:--:--";
  return d.toLocaleTimeString([], { hour12: false });
}

function pushHistory(payload) {
  history.value.push({
    reserve: Number(payload.reserve) || 0,
    waterheight: Number(payload.waterheight) || 0,
    percentage: Number(payload.percentage) || 0,
    radar: Number(payload.radar) || 0,
    timestamp: Number(payload.timestamp) || 0,
  });

  if (history.value.length > 10) {
    history.value.shift();
  }
}

function connectAndSubscribe() {
  try {
    Mqtt.connect();

    setTimeout(() => {
      Mqtt.subscribe("elet2415/radar");
    }, 1000);
  } catch (error) {
    console.log("Dashboard MQTT error:", error);
  }
}

watch(
  () => Mqtt.payload,
  (newPayload) => {
    if (!newPayload || typeof newPayload !== "object") return;

    if (
      newPayload.reserve === undefined &&
      newPayload.waterheight === undefined &&
      newPayload.percentage === undefined
    ) {
      return;
    }

    liveData.id = newPayload.id ?? "";
    liveData.type = newPayload.type ?? "";
    liveData.radar = Number(newPayload.radar ?? 0);
    liveData.waterheight = Number(newPayload.waterheight ?? 0);
    liveData.reserve = Number(newPayload.reserve ?? 0);
    liveData.percentage = Number(newPayload.percentage ?? 0);
    liveData.timestamp = Number(newPayload.timestamp ?? 0);

    pushHistory(newPayload);
  },
  { deep: true }
);

onMounted(() => {
  connectAndSubscribe();
});

onBeforeUnmount(() => {
  Mqtt.unsubcribeAll();
});
</script>

<style scoped>
.dashboard-wrap {
  background: #ffffff;
}

.dashboard-shell {
  border: 1px solid #d9d9d9;
  background: #fafafa;
}

.panel {
  border: 2px solid #1f1f1f;
  background: #ffffff;
  min-height: 100%;
}

.panel-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.panel-title {
  font-size: 1.65rem;
  font-weight: 700;
  color: #2f2f2f;
}

.menu-icon {
  font-size: 1.4rem;
  color: #666;
  line-height: 1;
}

.tank-box {
  width: 100%;
  display: flex;
  justify-content: center;
}

.tank-outline {
  width: 70px;
  height: 260px;
  border: 3px solid #929292;
  position: relative;
  background: #f5f5f5;
  overflow: visible;
}

.tank-fill {
  position: absolute;
  left: 0;
  bottom: 0;
  width: 100%;
  background: #57c339;
  transition: height 0.3s ease;
}

.tank-marker {
  position: absolute;
  left: calc(100% + 8px);
  transform: translateY(50%);
  display: flex;
  align-items: center;
  gap: 6px;
}

.tank-dot {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #57c339;
  border: 2px solid #4aa82f;
}

.tank-label {
  background: #8a8a8a;
  color: white;
  font-size: 0.7rem;
  padding: 2px 6px;
  border-radius: 4px;
}

.tank-caption {
  color: #999;
  font-weight: 600;
  font-size: 1rem;
}

.chart-area {
  width: 100%;
  position: relative;
}

.line-chart-svg {
  width: 100%;
  height: 320px;
  display: block;
}

.axis-label {
  font-size: 15px;
  fill: #555;
}

.axis-label.small {
  font-size: 12px;
}

.y-axis-label {
  position: absolute;
  transform: rotate(-90deg);
  transform-origin: left top;
  left: -6px;
  top: 210px;
  font-size: 0.9rem;
  color: #4b4b4b;
  font-weight: 600;
}

.chart-legend {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: -10px;
  color: #5a5a5a;
  font-size: 0.95rem;
}

.legend-line {
  display: inline-block;
  width: 18px;
  height: 4px;
  background: #5fb7ee;
}

.gauge-wrap {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 330px;
}

.gauge-svg {
  width: 100%;
  max-width: 560px;
  height: 280px;
  display: block;
}

.gauge-segment-red {
  fill: none;
  stroke: #e9534f;
  stroke-width: 18;
  stroke-linecap: butt;
}

.gauge-segment-yellow {
  fill: none;
  stroke: #d8d600;
  stroke-width: 18;
  stroke-linecap: butt;
}

.gauge-segment-green {
  fill: none;
  stroke: #57c339;
  stroke-width: 18;
  stroke-linecap: butt;
}

.gauge-tick-line {
  stroke: #ffffff;
  stroke-width: 2;
}

.gauge-tick-label {
  fill: #666;
  font-size: 14px;
  font-weight: 600;
}

.gauge-needle {
  stroke: #8d8d8d;
  stroke-width: 5;
  stroke-linecap: round;
}

.gauge-center-dot {
  fill: #8d8d8d;
}

.gauge-value-text {
  fill: #555;
  font-size: 24px;
  font-weight: 700;
}

.percent-panel {
  background: #eef3ff;
  text-align: center;
}

.water-level-title {
  font-size: 1.8rem;
  font-weight: 700;
  color: #5f7fd8;
  margin-top: 4px;
}

.water-level-subtitle {
  color: #8fa0c5;
  font-size: 1rem;
  margin-bottom: 20px;
}

.percent-circle-wrap {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 260px;
}

.percent-circle {
  width: 210px;
  height: 210px;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 30%, #ab3de0, #7f0ea5);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: inset 0 0 0 18px rgba(255, 255, 255, 0.15);
}

.percent-inner {
  font-size: 3.3rem;
  color: #ffffff;
  font-weight: 500;
}

@media (max-width: 960px) {
  .tank-outline {
    height: 220px;
  }

  .panel-title {
    font-size: 1.25rem;
  }

  .percent-circle {
    width: 180px;
    height: 180px;
  }

  .percent-inner {
    font-size: 2.5rem;
  }

  .gauge-svg {
    max-width: 100%;
    height: 240px;
  }
}
</style>