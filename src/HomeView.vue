<script setup lang="ts">
import { ref } from 'vue'

import FactorioGraph from './FactorioGraph.vue'
import { loadGame, type Game } from './Game'

const game = ref<Game | null>(null)
const loading = ref(false)

async function loadGameDefinition(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files !== null && target.files.length === 1) {
    loading.value = true
    game.value = await loadGame(target.files[0])
    loading.value = false
  }
}
</script>

<template>
  <div v-if="loading">Loading...</div>
  <div
    v-else-if="game !== null"
    style="display: flex; flex-direction: row; height: 100vh; width: 100%"
  >
    <div style="width: 1.5em; background-color: lightblue">L</div>
    <div style="flex: 1; overflow: hidden; display: flex; flex-direction: column">
      <div style="height: 1.5em; background-color: lightblue">T</div>
      <div style="flex: 1 1 75%; overflow: hidden">
        <FactorioGraph :game />
      </div>
      <div style="height: 1.5em; background-color: lightblue">B</div>
    </div>
    <div style="width: 1.5em; background-color: lightblue">R</div>
  </div>
  <div v-else>
    <input type="file" @change="loadGameDefinition" />
  </div>
</template>
