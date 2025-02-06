<script setup lang="ts">
import { nextTick, onMounted, reactive, ref, watch } from 'vue'
import { useElementSize } from '@vueuse/core'
import assert from './assert'
import type { Game } from './Game'

const props = defineProps<{
  game: Game
}>()

const container = ref<HTMLDivElement | null>(null)
const canvas = ref<HTMLCanvasElement | null>(null)

const { width, height } = useElementSize(container)

const { width: canvasWidth, height: canvasHeight } = useElementSize(canvas)

interface TransformationNodeContent {
  kind: 'transformation'
  name: string
  image: string
  crafters: string[]
}

interface ThingNodeContent {
  kind: 'thing'
  name: string
  image: string
}

type NodeContent = TransformationNodeContent | ThingNodeContent

interface GraphNode {
  left: number
  top: number
  content: NodeContent
  leftNeighbors: GraphNode[]
  rightNeighbors: GraphNode[]
}

const nodes = reactive<GraphNode[]>([])

const transformationNodes = reactive<Record<string, GraphNode>>({})
const thingNodes = reactive<Record<string, GraphNode>>({})

function findRecipeProducing(thingName: string): string | null {
  const thing = props.game.things[thingName]
  for (const recipe of thing.productOf) {
    if (transformationNodes[recipe.name] === undefined) {
      return recipe.name
    }
  }
  return null
}

function findRecipeConsuming(thingName: string): string | null {
  const thing = props.game.things[thingName]
  for (const recipe of thing.ingredientOf) {
    if (transformationNodes[recipe.name] === undefined) {
      return recipe.name
    }
  }
  return null
}

async function addRecipe(recipeName: string) {
  assert(transformationNodes[recipeName] === undefined)
  const transformation = props.game.transformations[recipeName]

  const newTransformationNodeIndex = nodes.length
  nodes.push({
    left: 0,
    top: 0,
    content: {
      kind: 'transformation',
      name: transformation.name,
      image: transformation.image,
      crafters: transformation.crafters.map((crafter) => crafter.image),
    },
    leftNeighbors: [],
    rightNeighbors: [],
  })
  const newTransformationNode = nodes[newTransformationNodeIndex]
  transformationNodes[transformation.name] = newTransformationNode
  const nodesToPosition = [newTransformationNodeIndex]

  for (const ingredient of transformation.ingredients) {
    let ingredientNode = thingNodes[ingredient.thing.name]
    if (ingredientNode === undefined) {
      const newIngredientNodeIndex = nodes.length
      nodes.push({
        left: 0,
        top: 0,
        content: {
          kind: 'thing',
          name: ingredient.thing.name,
          image: ingredient.thing.image,
        },
        leftNeighbors: [],
        rightNeighbors: [],
      })
      ingredientNode = nodes[newIngredientNodeIndex]
      thingNodes[ingredient.thing.name] = ingredientNode
      nodesToPosition.push(newIngredientNodeIndex)
    }
    ingredientNode.rightNeighbors.push(newTransformationNode)
    newTransformationNode.leftNeighbors.push(ingredientNode)
  }

  for (const product of transformation.products) {
    let productNode = thingNodes[product.thing.name]
    if (productNode === undefined) {
      const newProductNodeIndex = nodes.length
      nodes.push({
        left: 0,
        top: 0,
        content: {
          kind: 'thing',
          name: product.thing.name,
          image: product.thing.image,
        },
        leftNeighbors: [],
        rightNeighbors: [],
      })
      productNode = nodes[newProductNodeIndex]
      thingNodes[product.thing.name] = productNode
      nodesToPosition.push(newProductNodeIndex)
    }
    productNode.leftNeighbors.push(newTransformationNode)
    newTransformationNode.rightNeighbors.push(productNode)
  }

  await nextTick()

  for (const nodeIndex of nodesToPosition) {
    const node = nodes[nodeIndex]
    assert(nodeIndex < nodeElements.value.length)
    const element = nodeElements.value[nodeIndex]
    if (nodeIndex === 0) {
      node.left = width.value / 2 - element.offsetWidth / 2
      node.top = 20
    } else {
      const leftNeighborIndexes = node.leftNeighbors
        .map((left) => nodes.indexOf(left))
        .filter((index) => index < nodeIndex)
      const rightNeighborIndexes = node.rightNeighbors
        .map((right) => nodes.indexOf(right))
        .filter((index) => index < nodeIndex)
      assert(leftNeighborIndexes.length > 0 || rightNeighborIndexes.length > 0)

      const leftmostLeft = Math.min(...rightNeighborIndexes.map((right) => nodes[right].left))
      const rightmostRight = Math.max(
        ...leftNeighborIndexes.map(
          (left) => nodes[left].left + nodeElements.value[left].offsetWidth,
        ),
      )
      if (leftNeighborIndexes.length === 0) {
        node.left = leftmostLeft - element.offsetWidth - 50
      } else if (rightNeighborIndexes.length === 0) {
        node.left = rightmostRight + 50
      } else {
        node.left = (leftmostLeft + rightmostRight) / 2 - element.offsetWidth / 2
      }

      node.top = Math.max(
        ...leftNeighborIndexes.map((left) => nodes[left].top),
        ...rightNeighborIndexes.map((right) => nodes[right].top),
      )
      for (const rightNeighborIndex of rightNeighborIndexes) {
        if (rightNeighborIndex < nodeIndex) {
          for (const sibling of nodes[rightNeighborIndex].leftNeighbors) {
            const siblingIndex = nodes.indexOf(sibling)
            if (siblingIndex < nodeIndex) {
              node.top = Math.max(
                node.top,
                sibling.top + nodeElements.value[siblingIndex].offsetHeight + 20,
              )
            }
          }
        }
      }
      for (const leftNeighborIndex of leftNeighborIndexes) {
        if (leftNeighborIndex < nodeIndex) {
          for (const sibling of nodes[leftNeighborIndex].rightNeighbors) {
            const siblingIndex = nodes.indexOf(sibling)
            if (siblingIndex < nodeIndex) {
              node.top = Math.max(
                node.top,
                sibling.top + nodeElements.value[siblingIndex].offsetHeight + 20,
              )
            }
          }
        }
      }
    }
  }
}

function removeRecipeNode(recipeNodeIndex: number) {
  assert(recipeNodeIndex < nodes.length)
  const recipeNode = nodes[recipeNodeIndex]
  for (const left of recipeNode.leftNeighbors) {
    left.rightNeighbors.splice(left.rightNeighbors.indexOf(recipeNode), 1)
  }
  for (const right of recipeNode.rightNeighbors) {
    right.leftNeighbors.splice(right.leftNeighbors.indexOf(recipeNode), 1)
  }
  nodes.splice(recipeNodeIndex, 1)
  delete transformationNodes[recipeNode.content.name]

  const recipe = props.game.transformations[recipeNode.content.name]
  for (const ingredient of [...recipe.ingredients, ...recipe.products]) {
    const thingNode = thingNodes[ingredient.thing.name]
    if (thingNode !== undefined && thingNode.leftNeighbors.length === 0 && thingNode.rightNeighbors.length === 0) {
      nodes.splice(nodes.indexOf(thingNode), 1)
      delete thingNodes[ingredient.thing.name]
    }
  }
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

function startMoving(nodeIndex: number, e: PointerEvent) {
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
        for (const left of node.leftNeighbors) {
          edges.add([nodes.indexOf(left), nodes.indexOf(node)])
        }
        for (const right of node.rightNeighbors) {
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

function reset() {
  nodes.splice(0, nodes.length)
  Object.keys(transformationNodes).forEach((key) => delete transformationNodes[key])
  Object.keys(thingNodes).forEach((key) => delete thingNodes[key])
  addRecipe('electronic-circuit')
}

const stopInitialWatch = watch([width, height], ([width, height]) => {
  if (width !== 0 && height !== 0) {
    stopInitialWatch()
    reset()
  }
})

watch(() => props.game, reset)
</script>

<template>
  <div ref="container" class="container">
    <canvas v-if="width !== 0 && height !== 0" ref="canvas" :width :height></canvas>
    <div
      v-for="(node, nodeIndex) in nodes"
      ref="nodeElements"
      class="node"
      :style="{ top: `${node.top}px`, left: `${node.left}px` }"
      @pointerdown="(e) => startMoving(nodeIndex, e)"
    >
      <template v-if="node.content.kind === 'transformation'">
        <div>
          <button @pointerdown.stop @click="removeRecipeNode(nodeIndex)">X</button>
          <img width="48" height="48" :src="node.content.image" draggable="false" />
        </div>
        <div>
          <img v-for="crafter in node.content.crafters" width="24" height="24" :src="crafter" draggable="false" />
        </div>
      </template>
      <template v-else-if="node.content.kind === 'thing'">
        <template v-for="recipe of [findRecipeProducing(node.content.name)]">
          <button
            :disabled="recipe === null"
            @pointerdown.stop
            @click="(e) => (recipe !== null ? addRecipe(recipe) : undefined)"
          >
            +
          </button>
        </template>
        <img width="32" height="32" :src="node.content.image" draggable="false" />
        <template v-for="recipe of [findRecipeConsuming(node.content.name)]">
          <button
            :disabled="recipe === null"
            @pointerdown.stop
            @click="(e) => (recipe !== null ? addRecipe(recipe) : undefined)"
          >
            +
          </button>
        </template>
      </template>
      <template v-else>
        Unknown node kind: {{ ((c: never) => (c as any).kind)(node.content) }}
      </template>
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

div.node * {
  vertical-align: middle;
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
