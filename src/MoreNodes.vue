<script setup lang="ts">
import { nextTick, reactive, ref, watch } from 'vue'
import { useElementSize } from '@vueuse/core'
import assert from './assert'

const container = ref<HTMLDivElement | null>(null)
const canvas = ref<HTMLCanvasElement | null>(null)

const { width, height } = useElementSize(container)

const { width: canvasWidth, height: canvasHeight } = useElementSize(canvas)

interface GraphNode {
  left: number
  top: number
  text: string
  leftChildren: GraphNode[]
  rightChildren: GraphNode[]
}

const nodes = reactive<GraphNode[]>([
  { left: 300, top: 100, text: 'R1', leftChildren: [], rightChildren: [] },
  { left: 300, top: 200, text: 'R2', leftChildren: [], rightChildren: [] },
])

async function add(nodeIndex: number, dir: 'l' | 'r') {
  const node = nodes[nodeIndex]
  const element = nodeElements.value[nodeIndex]

  const siblings = dir === 'r' ? node.rightChildren : node.leftChildren
  const newNodeIndex = nodes.length
  nodes.push({
    left: node.left,
    top: node.top,
    text: node.text + `.${dir}${siblings.length + 1}`,
    leftChildren: dir === 'r' ? [node] : [],
    rightChildren: dir === 'l' ? [node] : [],
  })
  const newNode = nodes[newNodeIndex]
  siblings.push(newNode)

  assert(nodeElements.value.length <= newNodeIndex)

  await nextTick()

  assert(nodeElements.value.length > newNodeIndex)
  const newElement = nodeElements.value[newNodeIndex]

  // Fixed horizontal distance between node edges
  if (dir === 'r') {
    newNode.left = node.left + element.offsetWidth + 60
  } else {
    newNode.left = node.left - newElement.offsetWidth - 60
  }

  // Below all siblings (dumb approach -- there might be room between siblings -- but somewhat reliable)
  siblings.forEach((sibling) => {
    if (sibling !== newNode) {
      const siblingIndex = nodes.indexOf(sibling)
      const siblingElement = nodeElements.value[siblingIndex]
      if (sibling.top + siblingElement.offsetHeight >= newNode.top) {
        newNode.top = sibling.top + siblingElement.offsetHeight + 10
      }
    }
  })
}

async function addRight(nodeIndex: number) {
  add(nodeIndex, 'r')
}

async function addLeft(nodeIndex: number) {
  add(nodeIndex, 'l')
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
      initialX: node.left,
      initialY: node.top,
      startX: e.clientX,
      startY: e.clientY,
    }
  }
}

function move(e: PointerEvent) {
  assert(moving.value !== null)
  const node = moving.value.node
  node.left = Math.min(
    Math.max(0, moving.value.initialX + e.clientX - moving.value.startX),
    width.value - moving.value.element.offsetWidth,
  )
  node.top = Math.min(
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
        for (const left of node.leftChildren) {
          edges.add([nodes.indexOf(left), nodes.indexOf(node)])
        }
        for (const right of node.rightChildren) {
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
          nodes[orig].left + elements[orig].offsetWidth,
          nodes[orig].top + elements[orig].offsetHeight / 2,
        )
        ctx.bezierCurveTo(
          nodes[orig].left + elements[orig].offsetWidth + 50,
          nodes[orig].top + elements[orig].offsetHeight / 2,
          nodes[dest].left - 50,
          nodes[dest].top + elements[dest].offsetHeight / 2,
          nodes[dest].left,
          nodes[dest].top + elements[dest].offsetHeight / 2,
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
      :style="{ top: `${node.top}px`, left: `${node.left}px` }"
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
