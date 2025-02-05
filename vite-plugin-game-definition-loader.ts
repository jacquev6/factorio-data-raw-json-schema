import { createFilter } from '@rollup/pluginutils'
import fs from 'fs/promises'
import path from 'path'

import loadGameDefinition from './src/GameDefinition'


export default function vitePluginGameDefinitionLoader() {
  const filter = createFilter(['**/*.zip'])

  return {
    name: 'vite-plugin-game-definition-loader',
    async load(id: string) {
      if (filter(id)) {
        const filePath = path.resolve(id)
        const data = await fs.readFile(filePath)
        const blob = new Blob([data], { type: 'application/zip' })
        const game = await loadGameDefinition(blob)
        return `export default ${JSON.stringify(game)}`
      } else {
        return null
      }
    }
  }
}
