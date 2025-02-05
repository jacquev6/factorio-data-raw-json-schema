<script setup lang="ts">
import { computed, ref } from 'vue'

import FactorioGraph from './FactorioGraph.vue'
import { make as makeGame, type Game } from './Game'
// @ts-ignore @todo Fix typing of .zip modules imported through the Vite plugin
import baseGameDefinition_ from '../game-definitions/base-2.0.28.zip'
// @ts-ignore (Same as above)
import spaceAgeGameDefinition_ from '../game-definitions/space-age-2.0.28.zip'
import { load as loadGameDefinition, type GameDefinition } from './GameDefinition'

const baseGameDefinition: GameDefinition = baseGameDefinition_
const spaceAgeGameDefinition: GameDefinition = spaceAgeGameDefinition_

const gameDefinition = ref<GameDefinition>(baseGameDefinition_)
const game = computed(() => makeGame(gameDefinition.value))
const loading = ref(false)

async function changeGameDefinitionFile(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files !== null && target.files.length === 1) {
    loading.value = true
    gameDefinition.value = await loadGameDefinition(target.files[0])
    loading.value = false
  }
}
</script>

<template>
  <div style="display: flex; flex-direction: row; height: 100vh; width: 100%">
    <div style="width: 1.5em; background-color: lightblue">L</div>
    <div style="flex: 1; overflow: hidden; display: flex; flex-direction: column">
      <div style="background-color: lightblue">
        <input type="file" @change="changeGameDefinitionFile" />
        <button @click="gameDefinition = baseGameDefinition">Load base game</button>
        <wbr /> <wbr />
        <button @click="gameDefinition = spaceAgeGameDefinition">Load Space Age game</button>
      </div>
      <div style="flex: 1 1 75%; overflow: hidden">
        <div v-if="loading">Loading...</div>
        <FactorioGraph v-else :game />
      </div>
      <div style="height: 1.5em; background-color: lightblue">B</div>
    </div>
    <div style="width: 1.5em; background-color: lightblue">R</div>
  </div>
</template>
