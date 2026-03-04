<template>
  <v-container fluid class="pa-6 d-flex justify-center">
    <v-row justify="center" style="max-width: 900px; width: 100%;">
      <v-col cols="12" md="10" lg="8">
        <v-card class="pa-8 text-center" elevation="2" rounded="lg">
          <v-card-title class="justify-center text-h5 font-weight-bold">
            Combination
          </v-card-title>

          <v-card-subtitle class="mb-6">
            Enter your four digit passcode
          </v-card-subtitle>

          <div class="d-flex justify-center mb-6">
            <v-otp-input
              v-model="passcodeDigits"
              length="4"
              variant="outlined"
              base-color="grey-lighten-1"
              color="primary"
            />
          </div>

          <div class="d-flex justify-center mb-4">
            <v-btn
              color="primary"
              size="large"
              class="px-8"
              :loading="loading"
              @click="submitPasscode"
            >
              Submit
            </v-btn>
          </div>

          <v-alert
            v-if="message"
            :type="messageType"
            variant="tonal"
            class="mt-4 text-left"
          >
            {{ message }}
          </v-alert>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
// IMPORTS
import { ref, computed } from "vue";

// VARIABLES
const passcodeDigits = ref([]);
const loading = ref(false);
const message = ref("");
const messageType = ref("success");

// COMPUTED
const joinedPasscode = computed(() => {
  return Array.isArray(passcodeDigits.value)
    ? passcodeDigits.value.join("")
    : String(passcodeDigits.value || "");
});

// FUNCTIONS
const submitPasscode = async () => {
  message.value = "";

  const passcode = joinedPasscode.value;

  if (!/^\d{4}$/.test(passcode)) {
    messageType.value = "error";
    message.value = "Please enter exactly 4 digits.";
    return;
  }

  loading.value = true;

  try {
    const formData = new URLSearchParams();
    formData.append("passcode", passcode);

    const response = await fetch("/api/set/combination", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: formData.toString(),
    });

    const data = await response.json();

    if (data.status === "complete") {
      messageType.value = "success";
      message.value = "Passcode saved successfully.";
      passcodeDigits.value = [];
    } else {
      messageType.value = "error";
      message.value = "Failed to save passcode.";
    }
  } catch (error) {
    console.log("submitPasscode error:", error);
    messageType.value = "error";
    message.value = "Unable to reach backend.";
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.v-card {
  min-height: 320px;
}

:deep(.v-otp-input) {
  max-width: 320px;
}
</style>