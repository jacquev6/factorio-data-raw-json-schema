<script setup lang="ts">
import FactorioGraph from './FactorioGraph.vue'
import type { DataRaw } from './FactorioDataRaw'
import { makeGame } from './Game'
import dataRaw from '../script-output/data-raw-dump.json'

const game = makeGame(dataRaw as DataRaw)
</script>

<template>
  <div style="display: flex; flex-direction: row; height: 100vh; width: 100%">
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
</template>
