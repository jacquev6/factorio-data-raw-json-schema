<script setup lang="ts">
import { ref } from 'vue'

const canvas = ref<HTMLCanvasElement | null>(null)
</script>

<template>
  <div class="container">
    <canvas ref="canvas"></canvas>
    <div class="node">Node 1</div>
    <div class="node">Node 2</div>
  </div>
</template>

<style scoped>
div.container {
  outline: 1px solid black;
  position: relative;
}

div.node {
  position: absolute;
  top: 0;
  left: 0;
}
</style>
