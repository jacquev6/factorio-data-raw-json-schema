<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useElementSize } from '@vueuse/core'
import assert from './assert'

const container = ref<HTMLDivElement | null>(null)
const canvas = ref<HTMLCanvasElement | null>(null)

const { width, height } = useElementSize(container)

const { width: canvasWidth, height: canvasHeight } = useElementSize(canvas)

const positions = reactive({
  origin: { x: 40, y: 40 },
  destination: { x: 160, y: 80 },
})

const originStyle = computed(() => ({
  top: `${positions.origin.y}px`,
  left: `${positions.origin.x}px`,
}))

const destinationStyle = computed(() => ({
  top: `${positions.destination.y}px`,
  left: `${positions.destination.x}px`,
}))

const origin = ref<HTMLDivElement | null>(null)
const destination = ref<HTMLDivElement | null>(null)
const elements = { origin, destination }

interface Moving {
  name: 'origin' | 'destination'
  initialX: number
  initialY: number
  startX: number
  startY: number
}

const moving = ref<Moving | null>(null)

function startMoving(name: Moving['name'], e: PointerEvent) {
  moving.value = {
    name,
    initialX: positions[name].x,
    initialY: positions[name].y,
    startX: e.clientX,
    startY: e.clientY,
  }
}

function move(e: PointerEvent) {
  assert(moving.value !== null)
  const name = moving.value.name
  positions[name].x = Math.min(
    Math.max(0, moving.value.initialX + e.clientX - moving.value.startX),
    width.value - elements[name].value!.offsetWidth,
  )
  positions[name].y = Math.min(
    Math.max(0, moving.value.initialY + e.clientY - moving.value.startY),
    height.value - elements[name].value!.offsetHeight,
  )
}

function stopMoving() {
  moving.value = null
}

watch(
  [canvas, positions, origin, destination, canvasWidth, canvasHeight],
  ([canvas, positions, origin, destination]) => {
    if (canvas !== null && origin !== null && destination !== null) {
      const ctx = canvas.getContext('2d')
      assert(ctx !== null)
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      ctx.beginPath()
      ctx.lineWidth = 2
      ctx.lineCap = 'round'
      ctx.moveTo(
        positions.origin.x + origin.offsetWidth,
        positions.origin.y + origin.offsetHeight / 2,
      )
      ctx.bezierCurveTo(
        positions.origin.x + origin.offsetWidth + 50,
        positions.origin.y + origin.offsetHeight / 2,
        positions.destination.x - 50,
        positions.destination.y + destination.offsetHeight / 2,
        positions.destination.x,
        positions.destination.y + destination.offsetHeight / 2,
      )
      ctx.stroke()
    }
  },
  {
    deep: true,
  },
)
</script>

<template>
  <div ref="container" class="container">
    <canvas v-if="width !== 0 && height !== 0" ref="canvas" :width :height></canvas>
    <div
      ref="origin"
      class="node"
      :style="originStyle"
      @pointerdown="(e) => startMoving('origin', e)"
    >
      Origin
    </div>
    <div
      ref="destination"
      class="node"
      :style="destinationStyle"
      @pointerdown="(e) => startMoving('destination', e)"
    >
      Destination
    </div>
    <div
      v-if="moving !== null"
      class="frontdrop"
      @pointermove="move"
      @pointerup="stopMoving"
      @pointerleave="stopMoving"
    ></div>
  </div>
</template>

<style scoped>
* {
  user-select: none;
}

div.container {
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
}

div.node {
  cursor: move;
  position: absolute;
  padding: 2px;
  border: 2px solid black;
  background: white;
}

div.frontdrop {
  cursor: move;
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}
</style>
