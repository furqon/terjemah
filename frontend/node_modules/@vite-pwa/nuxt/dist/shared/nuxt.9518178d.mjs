import { addPluginTemplate, addTypeTemplate, addImports, createResolver, getNuxtVersion, resolveAlias, addPlugin, addComponent, extendWebpackConfig, addDevServerHandler, defineNuxtModule } from '@nuxt/kit';
import { lstat, writeFile, mkdir } from 'node:fs/promises';
import { join } from 'node:path';
import { VitePWA } from 'vite-plugin-pwa';
import { createHash } from 'node:crypto';
import { createReadStream } from 'node:fs';
import { resolve } from 'pathe';

const version = "1.1.1";

function configurePWAOptions(ctx, nitroConfig) {
  const { nuxt3_8, options, nuxt } = ctx;
  if (!options.outDir) {
    const publicDir = nitroConfig.output?.publicDir ?? nuxt.options.nitro?.output?.publicDir;
    options.outDir = publicDir ? resolve(publicDir) : resolve(nuxt.options.buildDir, "../.output/public");
  }
  if (options.devOptions?.enabled)
    options.devOptions.resolveTempFolder = () => resolve(nuxt.options.buildDir, "dev-sw-dist");
  let config;
  if (options.strategies === "injectManifest") {
    options.injectManifest = options.injectManifest ?? {};
    config = options.injectManifest;
  } else {
    options.strategies = "generateSW";
    options.workbox = options.workbox ?? {};
    if (options.registerType === "autoUpdate" && (options.client?.registerPlugin || options.injectRegister === "script" || options.injectRegister === "inline")) {
      options.workbox.clientsClaim = true;
      options.workbox.skipWaiting = true;
    }
    if (nuxt.options.dev) {
      options.workbox.navigateFallback = options.workbox.navigateFallback ?? nuxt.options.app.baseURL ?? "/";
      if (options.devOptions?.enabled && !options.devOptions.navigateFallbackAllowlist) {
        const baseURL = nuxt.options.app.baseURL;
        options.devOptions.navigateFallbackAllowlist = [baseURL ? new RegExp(`^${baseURL.replace(/[-/\\^$*+?.()|[\]{}]/g, "\\$&")}$`) : /^\/$/];
      }
    }
    if (!("navigateFallback" in options.workbox))
      options.workbox.navigateFallback = nuxt.options.app.baseURL ?? "/";
    config = options.workbox;
  }
  let buildAssetsDir = nuxt.options.app.buildAssetsDir ?? "_nuxt/";
  if (buildAssetsDir[0] === "/")
    buildAssetsDir = buildAssetsDir.slice(1);
  if (buildAssetsDir[buildAssetsDir.length - 1] !== "/")
    buildAssetsDir += "/";
  if (!("dontCacheBustURLsMatching" in config))
    config.dontCacheBustURLsMatching = new RegExp(buildAssetsDir);
  if (nuxt.options.experimental.payloadExtraction) {
    const enableGlobPatterns = nuxt.options.nitro.static || nuxt.options._generate || (!!nitroConfig.prerender?.routes?.length || Object.values(nitroConfig.routeRules ?? {}).some((r) => r.prerender));
    if (enableGlobPatterns) {
      config.globPatterns = config.globPatterns ?? [];
      config.globPatterns.push("**/_payload.json");
      if (options.strategies === "generateSW" && options.experimental?.enableWorkboxPayloadQueryParams) {
        options.workbox.runtimeCaching = options.workbox.runtimeCaching ?? [];
        options.workbox.runtimeCaching.push({
          urlPattern: /\/_payload\.json\?/,
          handler: "NetworkOnly",
          options: {
            plugins: [{
              /* this callback will be called when the fetch call fails */
              handlerDidError: async ({ request }) => {
                const url = new URL(request.url);
                url.search = "";
                return Response.redirect(url.href, 302);
              },
              /* this callback will prevent caching the response */
              cacheWillUpdate: async () => null
            }]
          }
        });
      }
    }
  }
  let appManifestFolder;
  if (nuxt3_8 && nuxt.options.experimental.appManifest) {
    config.globPatterns = config.globPatterns ?? [];
    appManifestFolder = `${buildAssetsDir}builds/`;
    config.globPatterns.push(`${appManifestFolder}**/*.json`);
  }
  if (!nuxt.options.dev && !config.manifestTransforms)
    config.manifestTransforms = [createManifestTransform(nuxt.options.app.baseURL ?? "/", options.outDir, appManifestFolder)];
  if (options.pwaAssets) {
    options.pwaAssets.integration = {
      baseUrl: nuxt.options.app.baseURL ?? "/",
      publicDir: ctx.publicDirFolder,
      outDir: options.outDir
    };
  }
  const integration = options.integration ?? {};
  const {
    beforeBuildServiceWorker: original,
    ...rest
  } = integration;
  options.integration = {
    ...rest,
    async beforeBuildServiceWorker(resolvedPwaOptions) {
      await original?.(resolvedPwaOptions);
      await nuxt.callHook("pwa:beforeBuildServiceWorker", resolvedPwaOptions);
    }
  };
}
function createManifestTransform(base, publicFolder, appManifestFolder) {
  return async (entries) => {
    entries.filter((e) => e.url.endsWith(".html")).forEach((e) => {
      const url = e.url.startsWith("/") ? e.url.slice(1) : e.url;
      if (url === "index.html") {
        e.url = base;
      } else {
        const parts = url.split("/");
        parts[parts.length - 1] = parts[parts.length - 1].replace(/\.html$/, "");
        e.url = parts.length > 1 ? parts.slice(0, parts.length - 1).join("/") : parts[0];
      }
    });
    if (appManifestFolder) {
      const regExp = /(\/)?[0-9a-f]{8}\b-[0-9a-f]{4}\b-[0-9a-f]{4}\b-[0-9a-f]{4}\b-[0-9a-f]{12}\.json$/i;
      entries.filter((e) => e.url.startsWith(appManifestFolder) && regExp.test(e.url)).forEach((e) => {
        e.revision = null;
      });
      const latest = `${appManifestFolder}latest.json`;
      const latestJson = resolve(publicFolder, latest);
      const data = await lstat(latestJson).catch(() => void 0);
      if (data?.isFile()) {
        const revision = await new Promise((resolve2, reject) => {
          const cHash = createHash("MD5");
          const stream = createReadStream(latestJson);
          stream.on("error", (err) => {
            reject(err);
          });
          stream.on("data", (chunk) => cHash.update(chunk));
          stream.on("end", () => {
            resolve2(cHash.digest("hex"));
          });
        });
        const latestEntry = entries.find((e) => e.url === latest);
        if (latestEntry)
          latestEntry.revision = revision;
        else
          entries.push({ url: latest, revision, size: data.size });
      } else {
        entries = entries.filter((e) => e.url !== latest);
      }
    }
    return { manifest: entries, warnings: [] };
  };
}

function addPwaTypeTemplate(filename, isNuxt4, content) {
  if (content?.length) {
    return addTypeTemplate({
      write: true,
      filename: `pwa-icons/${filename}.d.ts`,
      getContents: () => content
    }).dst;
  } else {
    return addTypeTemplate({
      write: true,
      getContents: () => generatePwaImageType(filename, isNuxt4),
      filename: `pwa-icons/${filename}.d.ts`
    }).dst;
  }
}
function pwaIcons(types) {
  return `// Generated by @vite-pwa/nuxt
import type { AppleSplashScreenLink, FaviconLink, HtmlLink, IconAsset } from '@vite-pwa/assets-generator/api'

export interface PWAAssetIconImage {
  width?: number
  height?: number
  key: string
  src: string
}
export type PWAAssetIcon<T extends HtmlLink> = Omit<IconAsset<T>, 'buffer'> & {
  asImage: PWAAssetIconImage
}
export interface PWAIcons {
  transparent: Record<${generateTypes(types?.transparent)}, PWAAssetIcon<HtmlLink>>
  maskable: Record<${generateTypes(types?.maskable)}, PWAAssetIcon<HtmlLink>>
  favicon: Record<${generateTypes(types?.favicon)}, PWAAssetIcon<FaviconLink>>
  apple: Record<${generateTypes(types?.apple)}, PWAAssetIcon<HtmlLink>>
  appleSplashScreen: Record<${generateTypes(types?.appleSplashScreen)}, PWAAssetIcon<AppleSplashScreenLink>>
}

declare module '#app' {
  interface NuxtApp {
    $pwaIcons?: PWAIcons
  }
}

declare module 'vue' {
  interface ComponentCustomProperties {
    $pwaIcons?: PWAIcons
  }
}

export {}
`;
}
function generatePwaImageType(filename, isNuxt4, names) {
  const propsName = `${filename}Props`;
  if (isNuxt4) {
    return `// Generated by @vite-pwa/nuxt
export interface ${propsName} {
  image: ${generateTypes(names)}
  alt?: string
  width?: number
  height?: number
  crossorigin?: '' | 'anonymous' | 'use-credentials'
  loading?: 'lazy' | 'eager'
  decoding?: 'async' | 'auto' | 'sync'
  nonce?: string
}
`;
  }
  return `// Generated by @vite-pwa/nuxt
export interface ${propsName} {
  image: ${generateTypes(names)}
  alt?: string
  width?: number
  height?: number
  crossorigin?: '' | 'anonymous' | 'use-credentials'
  loading?: 'lazy' | 'eager'
  decoding?: 'async' | 'auto' | 'sync'
  nonce?: string
}
type __VLS_NonUndefinedable<T> = T extends undefined ? never : T
type __VLS_TypePropsToRuntimeProps<T> = {
  [K in keyof T]-?: {} extends Pick<T, K> ? {
    type: import('vue').PropType<__VLS_NonUndefinedable<T[K]>>
  } : {
    type: import('vue').PropType<T[K]>
    required: true
  }
}
declare const _default: import('vue').DefineComponent<__VLS_TypePropsToRuntimeProps<${propsName}>, {}, unknown, {}, {}, import('vue').ComponentOptionsMixin, import('vue').ComponentOptionsMixin, {}, string, import('vue').PublicProps, Readonly<import('vue').ExtractPropTypes<__VLS_TypePropsToRuntimeProps<${propsName}>>>, {}, {}>
export default _default
`;
}
function generateTypes(types) {
  return types?.length ? types.map((name) => `'${name}'`).join(" | ") : "string";
}
function addPWAIconsPluginTemplate(pwaAssetsEnabled) {
  if (pwaAssetsEnabled) {
    addPluginTemplate({
      filename: "pwa-icons-plugin.ts",
      name: "vite-pwa:nuxt:pwa-icons-plugin",
      write: true,
      getContents: () => `// Generated by @vite-pwa/nuxt
import { defineNuxtPlugin } from '#imports'
import { pwaAssetsIcons } from 'virtual:pwa-assets/icons'
import type { PWAAssetIcon, PWAIcons } from '#build/pwa-icons/pwa-icons'

export default defineNuxtPlugin(() => {
  return {
    provide: {
      pwaIcons: {
        transparent: configureEntry('transparent'),
        maskable: configureEntry('maskable'),
        favicon: configureEntry('favicon'),
        apple: configureEntry('apple'),
        appleSplashScreen: configureEntry('appleSplashScreen')
      } satisfies PWAIcons
    }
  }
})

function configureEntry<K extends keyof PWAIcons>(key: K) {
  return Object.values(pwaAssetsIcons[key] ?? {}).reduce((acc, icon) => {
    const entry: PWAAssetIcon<any> = {
      ...icon,
      asImage: {
        src: icon.url,
        key: \`\${key}-\${icon.name}\`
      }
    }
    if (icon.width && icon.height) {
      entry.asImage.width = icon.width
      entry.asImage.height = icon.height
    }
    ;(acc as unknown as any)[icon.name] = entry
    return acc
  }, {} as PWAIcons[typeof key])
}
`
    });
  } else {
    addPluginTemplate({
      filename: "pwa-icons-plugin.ts",
      name: "vite-pwa:nuxt:pwa-icons-plugin",
      write: true,
      getContents: () => `// Generated by @vite-pwa/nuxt
import { defineNuxtPlugin } from '#imports'
import type { PWAIcons } from '#build/pwa-icons/pwa-icons'

export default defineNuxtPlugin(() => {
  return {
    provide: {
      pwaIcons: {
        transparent: {},
        maskable: {},
        favicon: {},
        apple: {},
        appleSplashScreen: {}
      } satisfies PWAIcons
    }
  }
})
`
    });
  }
}

async function registerPwaIconsTypes(ctx, runtimeDir) {
  const { options, nuxt, resolver } = ctx;
  const pwaAssets = options.pwaAssets && !options.pwaAssets.disabled;
  let dts;
  if (pwaAssets) {
    try {
      const { preparePWAIconTypes } = await import('../chunks/pwa-icons.mjs');
      dts = await preparePWAIconTypes(ctx);
    } catch {
      dts = void 0;
    }
  }
  nuxt.options.alias["#pwa"] = resolver.resolve(runtimeDir, "composables/index");
  nuxt.options.build.transpile.push("#pwa");
  addImports([
    "usePWA",
    "useTransparentPwaIcon",
    "useMaskablePwaIcon",
    "useFaviconPwaIcon",
    "useApplePwaIcon",
    "useAppleSplashScreenPwaIcon"
  ].map((key) => ({
    name: key,
    as: key,
    from: resolver.resolve(runtimeDir, "composables/index")
  })));
  const templates = [];
  const isNuxt4 = ctx.nuxt4;
  const dtsContent = dts?.dts;
  if (dtsContent) {
    templates.push(addTypeTemplate({
      write: true,
      filename: "pwa-icons/pwa-icons.d.ts",
      getContents: () => dtsContent
    }).dst);
  } else {
    templates.push(addTypeTemplate({
      write: true,
      filename: "pwa-icons/pwa-icons.d.ts",
      getContents: () => pwaIcons()
    }).dst);
  }
  templates.push(addPwaTypeTemplate("PwaTransparentImage", isNuxt4, dts?.transparent));
  templates.push(addPwaTypeTemplate("PwaMaskableImage", isNuxt4, dts?.maskable));
  templates.push(addPwaTypeTemplate("PwaFaviconImage", isNuxt4, dts?.favicon));
  templates.push(addPwaTypeTemplate("PwaAppleImage", isNuxt4, dts?.apple));
  templates.push(addPwaTypeTemplate("PwaAppleSplashScreenImage", isNuxt4, dts?.appleSplashScreen));
  if (ctx.nuxt4) {
    ctx.nuxt.hook("prepare:types", (context) => {
      const nodeReferences = context.nodeReferences;
      for (const path of templates) {
        nodeReferences.push({ path });
      }
    });
  }
  return !!dts;
}

async function regeneratePWA(_dir, pwaAssets, api) {
  if (pwaAssets) {
    const pwaAssetsGenerator = await api?.pwaAssetsGenerator();
    if (pwaAssetsGenerator)
      await pwaAssetsGenerator.generate();
  }
  if (!api || api.disabled)
    return;
  await api.generateSW();
}
async function writeWebManifest(dir, path, api, pwaAssets) {
  if (pwaAssets) {
    const pwaAssetsGenerator = await api.pwaAssetsGenerator();
    if (pwaAssetsGenerator)
      pwaAssetsGenerator.injectManifestIcons();
  }
  const manifest = api.generateBundle({})?.[path];
  if (manifest && "source" in manifest)
    await writeFile(resolve(dir, path), manifest.source, "utf-8");
}

async function doSetup(options, nuxt) {
  const resolver = createResolver(import.meta.url);
  const nuxtVersion = getNuxtVersion(nuxt).split(".").map((v) => Number.parseInt(v));
  const nuxt3_8 = nuxtVersion.length > 1 && (nuxtVersion[0] > 3 || nuxtVersion[0] === 3 && nuxtVersion[1] >= 8);
  const nuxt4 = nuxtVersion.length > 1 && nuxtVersion[0] >= 4;
  const future = nuxt.options.future;
  const ctx = {
    nuxt,
    nuxt3_8,
    nuxt4,
    // included at v3.12.0, then removed and included back again for v5 compatibility: we only need the layout to configure correctly the pwa assets image
    // https://github.com/nuxt/nuxt/releases/tag/v3.12.0
    nuxt4Compat: nuxt4 ? true : "compatibilityVersion" in future && typeof future.compatibilityVersion === "number" && future.compatibilityVersion >= 4,
    resolver: createResolver(import.meta.url),
    options,
    publicDirFolder: resolveAlias("public")
  };
  let vitePwaClientPlugin;
  const resolveVitePluginPWAAPI = () => {
    return vitePwaClientPlugin?.api;
  };
  const client = options.client ?? {
    registerPlugin: true,
    installPrompt: false,
    periodicSyncForUpdates: 0
  };
  const runtimeDir = resolver.resolve("../runtime");
  nuxt.options.build.transpile.push(runtimeDir);
  if (client.registerPlugin) {
    addPlugin({
      src: resolver.resolve(runtimeDir, "plugins/pwa.client"),
      mode: "client"
    });
  }
  const pwaAssetsEnabled = !!options.pwaAssets && options.pwaAssets.disabled !== true;
  addPWAIconsPluginTemplate(pwaAssetsEnabled);
  if (ctx.nuxt4) {
    await Promise.all([
      addComponent({
        name: "VitePwaManifest",
        filePath: resolver.resolve(runtimeDir, "components/VitePwaManifest")
      }),
      addComponent({
        name: "NuxtPwaManifest",
        filePath: resolver.resolve(runtimeDir, "components/VitePwaManifest")
      }),
      addComponent({
        name: "NuxtPwaAssets",
        filePath: resolver.resolve(runtimeDir, "components/NuxtPwaAssets")
      }),
      addComponent({
        name: "PwaAppleImage",
        filePath: resolver.resolve(runtimeDir, "components/nuxt4/PwaAppleImage")
      }),
      addComponent({
        name: "PwaAppleSplashScreenImage",
        filePath: resolver.resolve(runtimeDir, "components/nuxt4/PwaAppleSplashScreenImage")
      }),
      addComponent({
        name: "PwaFaviconImage",
        filePath: resolver.resolve(runtimeDir, "components/nuxt4/PwaFaviconImage")
      }),
      addComponent({
        name: "PwaMaskableImage",
        filePath: resolver.resolve(runtimeDir, "components/nuxt4/PwaMaskableImage")
      }),
      addComponent({
        name: "PwaTransparentImage",
        filePath: resolver.resolve(runtimeDir, "components/nuxt4/PwaTransparentImage")
      })
    ]);
  } else {
    await Promise.all([
      addComponent({
        name: "VitePwaManifest",
        filePath: resolver.resolve(runtimeDir, "components/VitePwaManifest")
      }),
      addComponent({
        name: "NuxtPwaManifest",
        filePath: resolver.resolve(runtimeDir, "components/VitePwaManifest")
      }),
      addComponent({
        name: "NuxtPwaAssets",
        filePath: resolver.resolve(runtimeDir, "components/NuxtPwaAssets")
      }),
      addComponent({
        name: "PwaAppleImage",
        filePath: resolver.resolve(runtimeDir, "components/PwaAppleImage.vue")
      }),
      addComponent({
        name: "PwaAppleSplashScreenImage",
        filePath: resolver.resolve(runtimeDir, "components/PwaAppleSplashScreenImage.vue")
      }),
      addComponent({
        name: "PwaFaviconImage",
        filePath: resolver.resolve(runtimeDir, "components/PwaFaviconImage.vue")
      }),
      addComponent({
        name: "PwaMaskableImage",
        filePath: resolver.resolve(runtimeDir, "components/PwaMaskableImage.vue")
      }),
      addComponent({
        name: "PwaTransparentImage",
        filePath: resolver.resolve(runtimeDir, "components/PwaTransparentImage.vue")
      })
    ]);
  }
  nuxt.hook("prepare:types", ({ references }) => {
    references.push({ path: resolver.resolve(runtimeDir, "plugins/types") });
    references.push({ types: "@vite-pwa/nuxt/configuration" });
    references.push({ types: "vite-plugin-pwa/vue" });
    references.push({ types: "vite-plugin-pwa/info" });
    references.push({ types: "vite-plugin-pwa/pwa-assets" });
  });
  const pwaAssets = await registerPwaIconsTypes(ctx, runtimeDir);
  const manifestDir = join(nuxt.options.buildDir, "manifests");
  nuxt.options.nitro.publicAssets = nuxt.options.nitro.publicAssets || [];
  nuxt.options.nitro.publicAssets.push({
    dir: manifestDir,
    maxAge: 0
  });
  nuxt.hook("nitro:init", (nitro) => {
    configurePWAOptions(ctx, nitro.options);
  });
  nuxt.hook("vite:extend", ({ config }) => {
    const plugin = config.plugins?.find((p) => p && typeof p === "object" && "name" in p && p.name === "vite-plugin-pwa");
    if (plugin)
      throw new Error("Remove vite-plugin-pwa plugin from Vite Plugins entry in Nuxt config file!");
  });
  nuxt.hook("vite:extendConfig", async (viteInlineConfig, { isClient }) => {
    viteInlineConfig.plugins = viteInlineConfig.plugins || [];
    const plugin = viteInlineConfig.plugins.find((p) => p && typeof p === "object" && "name" in p && p.name === "vite-plugin-pwa");
    if (plugin)
      throw new Error("Remove vite-plugin-pwa plugin from Vite Plugins entry in Nuxt config file!");
    if (options.manifest && isClient) {
      viteInlineConfig.plugins.push({
        name: "vite-pwa-nuxt:webmanifest:build",
        apply: "build",
        async writeBundle(_options, bundle) {
          if (options.disable || !bundle)
            return;
          const api = resolveVitePluginPWAAPI();
          if (api) {
            await mkdir(manifestDir, { recursive: true });
            await writeWebManifest(manifestDir, options.manifestFilename || "manifest.webmanifest", api, pwaAssets);
          }
        }
      });
    }
    if (isClient) {
      viteInlineConfig.plugins = viteInlineConfig.plugins || [];
      const configuration = "virtual:nuxt-pwa-configuration";
      const resolvedConfiguration = `\0${configuration}`;
      viteInlineConfig.plugins.push({
        name: "vite-pwa-nuxt:configuration",
        enforce: "pre",
        resolveId(id) {
          if (id === configuration)
            return resolvedConfiguration;
        },
        load(id) {
          if (id === resolvedConfiguration) {
            const display = typeof options.manifest !== "boolean" ? options.manifest?.display ?? "standalone" : "standalone";
            const installPrompt = typeof client.installPrompt === "undefined" || client.installPrompt === false ? void 0 : client.installPrompt === true || client.installPrompt.trim() === "" ? "vite-pwa:hide-install" : client.installPrompt.trim();
            return `export const enabled = ${client.registerPlugin}
export const display = '${display}'
export const installPrompt = ${JSON.stringify(installPrompt)}
export const periodicSyncForUpdates = ${typeof client.periodicSyncForUpdates === "number" ? client.periodicSyncForUpdates : 0}
`;
          }
        }
      });
    }
    const plugins = [...VitePWA(options).filter((p) => p.name !== "vite-plugin-pwa:build")];
    viteInlineConfig.plugins.push(plugins);
    if (isClient)
      vitePwaClientPlugin = plugins.find((p) => p.name === "vite-plugin-pwa");
  });
  extendWebpackConfig(() => {
    throw new Error("Webpack is not supported: @vite-pwa/nuxt module can only be used with Vite!");
  });
  if (nuxt.options.dev) {
    const webManifest = `${nuxt.options.app.baseURL}${options.devOptions?.webManifestUrl ?? options.manifestFilename ?? "manifest.webmanifest"}`;
    const devSw = `${nuxt.options.app.baseURL}dev-sw.js?dev-sw`;
    const workbox = `${nuxt.options.app.baseURL}workbox-`;
    const emptyHandle = (_req, _res, next) => {
      next();
    };
    nuxt.hook("vite:serverCreated", (viteServer, { isServer }) => {
      if (isServer)
        return;
      viteServer.middlewares.stack.push({ route: webManifest, handle: emptyHandle });
      viteServer.middlewares.stack.push({ route: devSw, handle: emptyHandle });
      if (options.pwaAssets) {
        viteServer.middlewares.stack.push({
          route: "",
          // @ts-expect-error just ignore
          handle: async (req, res, next) => {
            const url = req.url;
            if (!url)
              return next();
            if (!/\.(?:ico|png|svg|webp)$/.test(url))
              return next();
            const pwaAssetsGenerator = await resolveVitePluginPWAAPI()?.pwaAssetsGenerator();
            if (!pwaAssetsGenerator)
              return next();
            const icon = await pwaAssetsGenerator.findIconAsset(url);
            if (!icon)
              return next();
            if (icon.age > 0) {
              const ifModifiedSince = req.headers["if-modified-since"] ?? req.headers["If-Modified-Since"];
              const useIfModifiedSince = ifModifiedSince ? Array.isArray(ifModifiedSince) ? ifModifiedSince[0] : ifModifiedSince : void 0;
              if (useIfModifiedSince && new Date(icon.lastModified).getTime() / 1e3 >= new Date(useIfModifiedSince).getTime() / 1e3) {
                res.statusCode = 304;
                res.end();
                return;
              }
            }
            const buffer = await icon.buffer;
            res.setHeader("Age", icon.age / 1e3);
            res.setHeader("Content-Type", icon.mimeType);
            res.setHeader("Content-Length", buffer.length);
            res.setHeader("Last-Modified", new Date(icon.lastModified).toUTCString());
            res.statusCode = 200;
            res.end(buffer);
          }
        });
      }
    });
    if (!options.strategies || options.strategies === "generateSW") {
      nuxt.hook("vite:serverCreated", (viteServer, { isServer }) => {
        if (isServer)
          return;
        viteServer.middlewares.stack.push({ route: workbox, handle: emptyHandle });
      });
      if (options.devOptions?.suppressWarnings) {
        const suppressWarnings = `${nuxt.options.app.baseURL}suppress-warnings.js`;
        nuxt.hook("vite:serverCreated", (viteServer, { isServer }) => {
          if (isServer)
            return;
          viteServer.middlewares.stack.push({ route: suppressWarnings, handle: emptyHandle });
        });
      }
      const { sourcemap = nuxt.options.sourcemap.client === true } = options.workbox ?? {};
      if (sourcemap) {
        const swMap = `${nuxt.options.app.baseURL}${options.filename ?? "sw.js"}.map`;
        const resolvedSwMapFile = join(nuxt.options.buildDir, "dev-sw-dist", swMap);
        const worboxMap = `${nuxt.options.app.baseURL}workbox-`;
        addDevServerHandler({
          route: "",
          handler: await import('h3').then(({ defineLazyEventHandler }) => defineLazyEventHandler(async () => {
            const { dev } = await import('../chunks/dev.mjs');
            return dev(
              swMap,
              resolvedSwMapFile,
              worboxMap,
              nuxt.options.buildDir,
              nuxt.options.app.baseURL
            );
          }))
        });
      }
    }
  } else {
    if (!options.disable && options.registerWebManifestInRouteRules) {
      nuxt.hook("nitro:config", async (nitroConfig) => {
        nitroConfig.routeRules = nitroConfig.routeRules || {};
        let swName = options.filename || "sw.js";
        if (options.strategies === "injectManifest" && swName.endsWith(".ts"))
          swName = swName.replace(/\.ts$/, ".js");
        nitroConfig.routeRules[`${nuxt.options.app.baseURL}${swName}`] = {
          headers: {
            "Cache-Control": "public, max-age=0, must-revalidate"
          }
        };
        if (options.manifest) {
          nitroConfig.routeRules[`${nuxt.options.app.baseURL}${options.manifestFilename ?? "manifest.webmanifest"}`] = {
            headers: {
              "Content-Type": "application/manifest+json",
              "Cache-Control": "public, max-age=0, must-revalidate"
            }
          };
        }
      });
    }
    if (nuxt3_8) {
      nuxt.hook("nitro:build:public-assets", async () => {
        await regeneratePWA(
          options.outDir,
          pwaAssets,
          resolveVitePluginPWAAPI()
        );
      });
    } else {
      nuxt.hook("nitro:init", (nitro) => {
        nitro.hooks.hook("rollup:before", async () => {
          await regeneratePWA(
            options.outDir,
            pwaAssets,
            resolveVitePluginPWAAPI()
          );
        });
      });
      if (nuxt.options.nitro.static || nuxt.options._generate) {
        nuxt.hook("close", async () => {
          await regeneratePWA(
            options.outDir,
            pwaAssets,
            resolveVitePluginPWAAPI()
          );
        });
      }
    }
  }
}

const module = defineNuxtModule({
  meta: {
    name: "@vite-pwa/nuxt",
    configKey: "pwa",
    compatibility: {
      nuxt: ">=3.6.5"
    },
    version
  },
  defaults: (nuxt) => ({
    base: nuxt.options.app.baseURL,
    scope: nuxt.options.app.baseURL,
    injectRegister: false,
    includeManifestIcons: false,
    registerPlugin: true,
    writePlugin: false,
    client: {
      registerPlugin: true,
      installPrompt: false,
      periodicSyncForUpdates: 0
    }
  }),
  async setup(options, nuxt) {
    await doSetup(options, nuxt);
  }
});

export { generatePwaImageType as g, module as m, pwaIcons as p };
