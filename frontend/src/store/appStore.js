import { defineStore } from "pinia";
import { ref } from "vue";

export const useAppStore = defineStore(
  "app",
  () => {
    // STATES
    const reserveData = ref([]);
    const averageReserve = ref(0);

    // ACTIONS
    const getReserveRange = async (start, end) => {
      try {
        const response = await fetch(`/api/reserve/${start}/${end}`);
        const data = await response.json();

        if (data.status === "found") {
          reserveData.value = Array.isArray(data.data) ? data.data : [];
          return reserveData.value;
        }

        reserveData.value = [];
        return [];
      } catch (error) {
        console.log("getReserveRange error:", error);
        reserveData.value = [];
        return [];
      }
    };

    const getAverageReserve = async (start, end) => {
      try {
        const response = await fetch(`/api/avg/${start}/${end}`);
        const data = await response.json();

        if (data.status === "found") {
          averageReserve.value = Number(data.data) || 0;
          return averageReserve.value;
        }

        averageReserve.value = 0;
        return 0;
      } catch (error) {
        console.log("getAverageReserve error:", error);
        averageReserve.value = 0;
        return 0;
      }
    };

    return {
      reserveData,
      averageReserve,
      getReserveRange,
      getAverageReserve,
    };
  },
  { persist: true }
);