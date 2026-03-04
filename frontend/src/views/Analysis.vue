<template>
  <v-container fluid class="analysis-page">
    <v-row justify="center" class="ma-0">
      <v-col cols="12" xl="10" lg="10" md="11" class="pa-0">
        <v-sheet class="analysis-shell" rounded="0" elevation="0">
          <!-- TOP ROW -->
          <v-row class="ma-0 top-row" align="start">
            <!-- LEFT: DATE INPUTS + BUTTON -->
            <v-col cols="12" md="3" class="pa-3">
              <v-sheet class="mini-panel pa-3" rounded="sm" elevation="0">
                <div class="field-label">Start Date</div>
                <v-text-field
                  v-model="startDate"
                  type="date"
                  density="compact"
                  variant="plain"
                  hide-details
                  class="date-field"
                />
              </v-sheet>

              <v-sheet class="mini-panel pa-3 mt-3" rounded="sm" elevation="0">
                <div class="field-label">End Date</div>
                <v-text-field
                  v-model="endDate"
                  type="date"
                  density="compact"
                  variant="plain"
                  hide-details
                  class="date-field"
                />
              </v-sheet>

              <div class="mt-3 text-center text-md-left">
                <v-btn
                  class="analyze-btn"
                  color="grey-lighten-2"
                  variant="flat"
                  :loading="loading"
                  @click="loadAnalysis"
                >
                  Analyze
                </v-btn>
              </div>
            </v-col>

            <!-- RIGHT: AVERAGE CARD -->
            <v-col cols="12" md="9" class="pa-3 pt-md-3 pl-md-0">
              <v-card class="avg-card" rounded="sm" elevation="0">
                <div class="avg-title">Average</div>
                <div class="avg-subtitle">For the selected period</div>

                <div class="avg-value-row">
                  <span class="avg-value">{{ averageReserveDisplay }}</span>
                  <span class="avg-unit">Gal</span>
                </div>
              </v-card>
            </v-col>
          </v-row>

          <!-- LINE GRAPH -->
          <v-row class="ma-0">
            <v-col cols="12" class="px-3 pb-3">
              <v-sheet class="chart-panel" rounded="0" elevation="0">
                <div id="reserveChart"></div>
              </v-sheet>
            </v-col>
          </v-row>

          <!-- SCATTER GRAPH -->
          <v-row class="ma-0">
            <v-col cols="12" class="px-3 pb-5">
              <v-sheet class="chart-panel" rounded="0" elevation="0">
                <div id="scatterChart"></div>
              </v-sheet>
            </v-col>
          </v-row>
        </v-sheet>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from "vue";
import Highcharts from "highcharts";
import Exporting from "highcharts/modules/exporting";
import { useAppStore } from "@/store/appStore";

Exporting(Highcharts);

const AppStore = useAppStore();

const loading = ref(false);
const records = ref([]);
const averageReserve = ref(0);

const startDate = ref("");
const endDate = ref("");

let reserveChart = null;
let scatterChart = null;

function pad(n) {
  return String(n).padStart(2, "0");
}

function toDateOnly(date) {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

function toTimestampStart(dateStr) {
  if (!dateStr) return 0;
  const d = new Date(`${dateStr}T00:00:00`);
  return Math.floor(d.getTime() / 1000);
}

function toTimestampEnd(dateStr) {
  if (!dateStr) return 0;
  const d = new Date(`${dateStr}T23:59:59`);
  return Math.floor(d.getTime() / 1000);
}

function setDefaultRange() {
  const end = new Date();
  const start = new Date();
  start.setDate(end.getDate() - 2);

  startDate.value = toDateOnly(start);
  endDate.value = toDateOnly(end);
}

const averageReserveDisplay = computed(() => {
  const val = Number(averageReserve.value) || 0;
  return val.toFixed(1);
});

function createCharts() {
  reserveChart = Highcharts.chart("reserveChart", {
    chart: {
      type: "line",
      height: 330,
      backgroundColor: "#ffffff",
      spacingTop: 10,
      spacingLeft: 10,
      spacingRight: 10,
      spacingBottom: 10,
    },
    title: {
      text: "Water Management Analysis",
      align: "left",
      style: {
        fontSize: "16px",
        fontWeight: "700",
        color: "#333333",
      },
    },
    credits: {
      enabled: true,
    },
    exporting: {
      enabled: true,
    },
    legend: {
      enabled: true,
      align: "center",
      verticalAlign: "bottom",
    },
    xAxis: {
      type: "datetime",
      title: {
        text: "Time",
        style: { fontSize: "12px" },
      },
      lineColor: "#666",
      tickColor: "#666",
    },
    yAxis: {
      min: 0,
      title: {
        text: "Water Reserve",
        style: { fontSize: "12px" },
      },
      labels: {
        format: "{value} Gal",
      },
      gridLineColor: "#e6e6e6",
    },
    tooltip: {
      shared: true,
      xDateFormat: "%H:%M:%S",
      valueSuffix: " Gal",
    },
    plotOptions: {
      line: {
        marker: {
          enabled: true,
          radius: 2,
        },
        lineWidth: 2,
      },
      series: {
        animation: false,
      },
    },
    series: [
      {
        name: "Reserve",
        type: "line",
        data: [],
      },
    ],
  });

  scatterChart = Highcharts.chart("scatterChart", {
    chart: {
      type: "scatter",
      zoomType: "xy",
      height: 330,
      backgroundColor: "#ffffff",
      spacingTop: 10,
      spacingLeft: 10,
      spacingRight: 10,
      spacingBottom: 10,
    },
    title: {
      text: "Height and Water Level Correlation Analysis",
      align: "left",
      style: {
        fontSize: "16px",
        fontWeight: "700",
        color: "#333333",
      },
    },
    credits: {
      enabled: true,
    },
    exporting: {
      enabled: true,
    },
    legend: {
      enabled: true,
      align: "center",
      verticalAlign: "bottom",
    },
    xAxis: {
      title: {
        text: "Water Height",
        style: { fontSize: "12px" },
      },
      labels: {
        format: "{value} in",
      },
      min: 0,
      lineColor: "#666",
      tickColor: "#666",
      gridLineWidth: 0,
    },
    yAxis: {
      title: {
        text: "Height",
        style: { fontSize: "12px" },
      },
      labels: {
        format: "{value} in",
      },
      min: 0,
      gridLineColor: "#e6e6e6",
    },
    tooltip: {
      pointFormat:
        "Water Height: <b>{point.x:.1f} in</b><br/>Height: <b>{point.y:.1f} in</b>",
    },
    plotOptions: {
      scatter: {
        marker: {
          radius: 3,
        },
      },
      series: {
        animation: false,
      },
    },
    series: [
      {
        name: "Analysis",
        type: "scatter",
        data: [],
      },
    ],
  });
}

function updateCharts() {
  if (!reserveChart || !scatterChart) return;

  const reserveSeries = records.value.map((item) => [
    Number(item.timestamp) * 1000,
    Number(item.reserve) || 0,
  ]);

  const scatterSeries = records.value.map((item) => ({
    x: Number(item.waterheight) || 0,
    y: Number(item.radar) || 0,
  }));

  reserveChart.series[0].setData(reserveSeries, true);
  scatterChart.series[0].setData(scatterSeries, true);
}

async function loadAnalysis() {
  const startTs = toTimestampStart(startDate.value);
  const endTs = toTimestampEnd(endDate.value);

  if (!startTs || !endTs || endTs < startTs) {
    records.value = [];
    averageReserve.value = 0;
    updateCharts();
    return;
  }

  loading.value = true;

  try {
    const reserveRows = await AppStore.getReserveRange(startTs, endTs);
    const avgValue = await AppStore.getAverageReserve(startTs, endTs);

    records.value = reserveRows;
    averageReserve.value = avgValue;

    updateCharts();
  } catch (error) {
    console.log("Analysis load error:", error);
    records.value = [];
    averageReserve.value = 0;
    updateCharts();
  } finally {
    loading.value = false;
  }
}

onMounted(async () => {
  setDefaultRange();
  await nextTick();
  createCharts();
});
</script>

<style scoped>
.analysis-page {
  background: #ffffff;
  min-height: 100%;
  padding-top: 18px;
}

.analysis-shell {
  border: 1px solid #c7d5ea;
  background: #ffffff;
  min-height: 760px;
}

.top-row {
  padding-top: 18px;
}

.mini-panel {
  background: #f3f3f3;
  border: 1px solid #ededed;
  max-width: 150px;
}

.field-label {
  font-size: 11px;
  color: #8a8a8a;
  margin-bottom: 2px;
}

:deep(.date-field input) {
  font-size: 28px;
  color: #4a4a4a;
  padding-top: 0 !important;
  padding-bottom: 0 !important;
}

:deep(.date-field .v-field__input) {
  min-height: 28px !important;
  padding: 0 !important;
}

.analyze-btn {
  text-transform: none;
  color: #4b4b4b;
  min-width: 92px;
  box-shadow: none;
}

.avg-card {
  width: 100%;
  min-height: 152px;
  background: #f3f3f3;
  border: 1px solid #ededed;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.avg-title {
  font-size: 17px;
  font-weight: 700;
  color: #4a4a4a;
  line-height: 1.1;
}

.avg-subtitle {
  font-size: 12px;
  color: #9c9c9c;
  margin-top: 2px;
}

.avg-value-row {
  margin-top: 8px;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: 6px;
}

.avg-value {
  font-size: 72px;
  line-height: 1;
  font-weight: 300;
  color: #1f1f1f;
}

.avg-unit {
  font-size: 18px;
  color: #7a7a7a;
  margin-bottom: 10px;
}

.chart-panel {
  border: 2px solid #343434;
  background: #ffffff;
  padding: 6px 6px 2px 6px;
}

#reserveChart {
  height: 350px;
  width: 100%;
}

#scatterChart {
  height: 330px;
  width: 100%;
}

@media (max-width: 960px) {
  .mini-panel {
    max-width: 100%;
  }

  .avg-value {
    font-size: 54px;
  }
}
</style>