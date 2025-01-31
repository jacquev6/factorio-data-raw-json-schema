<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
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
  left: GraphNode[]
  right: GraphNode[]
}

const nodes = reactive<GraphNode[]>([
  { x: 200, y: 100, text: 'R1', left: [], right: [] },
  { x: 200, y: 200, text: 'R2', left: [], right: [] },
])

function addRight(nodeIndex: number) {
  const node = nodes[nodeIndex]
  nodes.push({
    x: node.x + 100,
    y: node.y,
    text: node.text + `.r${node.right.length + 1}`,
    left: [node],
    right: [],
  })
  node.right.push(nodes[nodes.length - 1])
}

function addLeft(nodeIndex: number) {
  const node = nodes[nodeIndex]
  nodes.push({
    x: node.x - 100,
    y: node.y,
    text: node.text + `.l${node.left.length + 1}`,
    left: [],
    right: [node],
  })
  node.left.push(nodes[nodes.length - 1])
}

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

function maybeStartMoving(nodeIndex: number, e: PointerEvent) {
  if (e.target === nodeElements.value[nodeIndex]) {
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
  [canvas, nodes, nodeElements, canvasWidth, canvasHeight],
  ([canvas, nodes, elements]) => {
    if (canvas !== null && elements.length === nodes.length) {
      const edges = new Set<[number, number]>()
      for (const node of nodes) {
        for (const left of node.left) {
          edges.add([nodes.indexOf(left), nodes.indexOf(node)])
        }
        for (const right of node.right) {
          edges.add([nodes.indexOf(node), nodes.indexOf(right)])
        }
      }

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
      @pointerdown="(e) => maybeStartMoving(nodeIndex, e)"
    >
      <button @click="addLeft(nodeIndex)">+</button>
      {{ node.text }}
      <button @click="addRight(nodeIndex)">+</button>
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
