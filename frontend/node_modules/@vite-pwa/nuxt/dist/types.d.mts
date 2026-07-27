import type { ModuleHooks, ModuleRuntimeHooks } from './module.js'

declare module '#app' {
  interface RuntimeNuxtHooks extends ModuleRuntimeHooks {}
}

declare module '@nuxt/schema' {
  interface NuxtHooks extends ModuleHooks {}
}

declare module 'nuxt/schema' {
  interface NuxtHooks extends ModuleHooks {}
}

export { type ClientOptions, type ModuleHooks, type ModuleOptions, type ModuleRuntimeHooks, type PwaModuleHooks, type PwaModuleOptions, default } from './module.js'
