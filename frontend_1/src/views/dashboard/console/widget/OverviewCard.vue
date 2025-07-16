<template>
  <div class="overview-card art-custom-card">
    <MeetingOverview />
    <UnreadMessages style="margin-top:16px" />
  </div>
</template>
<script setup lang="ts">
import MeetingOverview from './MeetingOverview.vue'
import UnreadMessages from './UnreadMessages.vue'
</script>
<style scoped lang="scss">
.overview-card {
  padding: 0; // 子组件已带padding
}
</style> 