import * as _nuxt_schema from '@nuxt/schema';
import { HookResult } from '@nuxt/schema';
import { VitePWAOptions, ResolvedVitePWAOptions } from 'vite-plugin-pwa';

interface ClientOptions {
    /**
     * Exposes the plugin: defaults to true.
     */
    registerPlugin?: boolean;
    /**
     * Registers a periodic sync for updates interval: value in seconds.
     */
    periodicSyncForUpdates?: number;
    /**
     * Will prevent showing native PWA install prompt: defaults to false.
     *
     * When set to true or no empty string, the native PWA install prompt will be prevented.
     *
     * When set to a string, it will be used as the key in `localStorage` to prevent show the PWA install prompt widget.
     *
     * When set to true, the key used will be `vite-pwa:hide-install`.
     */
    installPrompt?: boolean | string;
}
interface PwaModuleOptions extends Partial<VitePWAOptions> {
    /**
     * Experimental features.
     */
    experimental?: {
        /**
         * NOTE: this option will be ignored if using the `injectManifest` strategy or when Nuxt experimental payload
         * extraction is disabled.
         *
         * Enable custom runtime caching to resolve the payload.json requests with query parameters when offline:
         * - Workbox doesn't allow to configure `precacheAndRoute` `urlManipulation` option when using the `generateSW` strategy.
         * - Nuxt SSG will generate a payload.json file and will fetch it with a query parameter.
         * - The service worker cannot resolve the payload.json request with query parameters, and you won't get the payload when offline.
         *
         * Enabling this option will add a custom runtime caching handler to the service worker to resolve the payload files
         * with query parameters when offline: the runtime caching handler will redirect to the payload.json file without
         * query parameters when the original request fails.
         *
         * If you're using `injectManifest` strategy, you can fix the issue in your custom service worker adding the
         * following `urlManipulation` callback to the `precacheAndRouter` call:
         * ```ts
         * // self.__WB_MANIFEST is the default injection point
         * precacheAndRoute(
         *   self.__WB_MANIFEST,
         *   {
         *     urlManipulation: ({ url }) => {
         *       const urls: URL[] = []
         *       if (url.pathname.endsWith('_payload.json')) {
         *         const newUrl = new URL(url.href)
         *         newUrl.search = ''
         *         urls.push(newUrl)
         *       }
         *       return urls
         *     }
         *   }
         * )
         * ```
         */
        enableWorkboxPayloadQueryParams?: true;
    };
    registerWebManifestInRouteRules?: boolean;
    /**
     * Writes the plugin to disk: defaults to false (debug).
     */
    writePlugin?: boolean;
    /**
     * Options for plugin.
     */
    client?: ClientOptions;
}
interface PwaModuleHooks {
    'pwa:beforeBuildServiceWorker': (options: ResolvedVitePWAOptions) => HookResult;
}

interface ModuleOptions extends PwaModuleOptions {
}
interface ModuleHooks extends PwaModuleHooks {
}
interface ModuleRuntimeHooks {
    /**
     * Emitted when the service worker is registered
     * @param data The url and the optional service worker registration object
     */
    'service-worker:registered': (data: {
        url: string;
        registration?: ServiceWorkerRegistration;
    }) => HookResult;
    /**
     * Emitted when the service worker registration fails
     * @param data The optional error object
     */
    'service-worker:registration-failed': (data: {
        error?: unknown;
    }) => HookResult;
    /**
     * Emitted when the service worker is activated
     * @param data The url and the service worker registration object
     */
    'service-worker:activated': (data: {
        url: string;
        registration: ServiceWorkerRegistration;
    }) => HookResult;
}
declare const _default: _nuxt_schema.NuxtModule<ModuleOptions>;

export { type ClientOptions, type ModuleHooks, type ModuleOptions, type ModuleRuntimeHooks, type PwaModuleHooks, type PwaModuleOptions, _default as default };
