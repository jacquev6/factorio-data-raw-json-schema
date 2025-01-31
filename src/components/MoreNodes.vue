<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useElementSize } from '@vueuse/core'

function assert(condition: boolean): asserts condition {
  console.assert(condition)
}

const container = ref<HTMLDivElement | null>(null)
const canvas = ref<HTMLCanvasElement | null>(null)

const { width, height } = useElementSize(container)

const { width: canvasWidth, height: canvasHeight } = useElementSize(canvas)

interface GraphNode {
  x: number
  y: number
  text: string
}

const nodes = reactive<GraphNode[]>([
  { x: 40, y: 40, text: 'Alpha' },
  { x: 160, y: 80, text: 'Bravo' },
  { x: 80, y: 160, text: 'Charlie' },
  { x: 200, y: 200, text: 'Delta' },
])

const edges = reactive([
  [0, 1],
  [2, 1],
  [2, 3],
])

const nodeElements = ref<HTMLDivElement[]>([])

interface Moving {
  node: GraphNode
  element: HTMLDivElement
  initialX: number
  initialY: number
  startX: number
  startY: number
}

const moving = ref<Moving | null>(null)

function startMoving(nodeIndex: number, e: PointerEvent) {
  const node = nodes[nodeIndex]
  moving.value = {
    node,
    element: nodeElements.value[nodeIndex],
    initialX: node.x,
    initialY: node.y,
    startX: e.clientX,
    startY: e.clientY,
  }
}

function move(e: PointerEvent) {
  assert(moving.value !== null)
  const node = moving.value.node
  node.x = Math.min(
    Math.max(0, moving.value.initialX + e.clientX - moving.value.startX),
    width.value - moving.value.element.offsetWidth,
  )
  node.y = Math.min(
    Math.max(0, moving.value.initialY + e.clientY - moving.value.startY),
    height.value - moving.value.element.offsetHeight,
  )
}

function stopMoving() {
  moving.value = null
}

watch(
  [canvas, nodes, nodeElements, edges, canvasWidth, canvasHeight],
  ([canvas, nodes, elements, edges]) => {
    if (canvas !== null && elements.length === nodes.length) {
      const ctx = canvas.getContext('2d')
      assert(ctx !== null)
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      ctx.beginPath()
      ctx.lineWidth = 2
      ctx.lineCap = 'round'

      for (const [orig, dest] of edges) {
        ctx.moveTo(
          nodes[orig].x + elements[orig].offsetWidth,
          nodes[orig].y + elements[orig].offsetHeight / 2,
        )
        ctx.bezierCurveTo(
          nodes[orig].x + elements[orig].offsetWidth + 50,
          nodes[orig].y + elements[orig].offsetHeight / 2,
          nodes[dest].x - 50,
          nodes[dest].y + elements[dest].offsetHeight / 2,
          nodes[dest].x,
          nodes[dest].y + elements[dest].offsetHeight / 2,
        )
      }
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
      v-for="(node, nodeIndex) in nodes"
      ref="nodeElements"
      class="node"
      :style="{ top: `${node.y}px`, left: `${node.x}px` }"
      @pointerdown="(e) => startMoving(nodeIndex, e)"
    >
      {{ node.text }}
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
