import fs from 'node:fs';
import { readFile, access } from 'node:fs/promises';
import process from 'node:process';
import { instructions } from '@vite-pwa/assets-generator/api/instructions';
import { loadConfig } from '@vite-pwa/assets-generator/config';
import { relative, basename, resolve } from 'pathe';
import { p as pwaIcons, g as generatePwaImageType } from '../shared/nuxt.9518178d.mjs';
import '@nuxt/kit';
import 'node:path';
import 'vite-plugin-pwa';
import 'node:crypto';

async function preparePWAIconTypes(ctx) {
  const { options, nuxt } = ctx;
  if (!options.pwaAssets || options.pwaAssets.disabled)
    return;
  const configuration = await resolvePWAAssetsOptions(ctx);
  if (!configuration || configuration.disabled)
    return;
  const root = nuxt.options.vite.root ?? process.cwd();
  const { config, sources } = await loadConfiguration(root, configuration);
  if (!config.preset)
    return;
  const {
    preset,
    images,
    headLinkOptions: userHeadLinkOptions
  } = config;
  if (!images)
    return;
  if (Array.isArray(images) && (!images.length || images.length > 1))
    return;
  const useImage = Array.isArray(images) ? images[0] : images;
  const imageFile = await tryToResolveImage(ctx, useImage);
  const publicDir = ctx.publicDirFolder;
  const imageName = relative(publicDir, imageFile);
  const xhtml = userHeadLinkOptions?.xhtml === true;
  const includeId = userHeadLinkOptions?.includeId === true;
  const assetsInstructions = await instructions({
    imageResolver: () => readFile(imageFile),
    imageName,
    preset,
    faviconPreset: userHeadLinkOptions?.preset,
    htmlLinks: { xhtml, includeId },
    basePath: nuxt.options.app.baseURL ?? "/",
    resolveSvgName: userHeadLinkOptions?.resolveSvgName ?? ((name) => basename(name))
  });
  const transparentNames = Object.values(assetsInstructions.transparent).map(({ name }) => name);
  const maskableNames = Object.values(assetsInstructions.maskable).map(({ name }) => name);
  const faviconNames = Object.values(assetsInstructions.favicon).map(({ name }) => name);
  const appleNames = Object.values(assetsInstructions.apple).map(({ name }) => name);
  const appleSplashScreenNames = Object.values(assetsInstructions.appleSplashScreen).map(({ name }) => name);
  const dts = {
    dts: pwaIcons({
      transparent: transparentNames,
      maskable: maskableNames,
      favicon: faviconNames,
      apple: appleNames,
      appleSplashScreen: appleSplashScreenNames
    }),
    transparent: generatePwaImageType("PwaTransparentImage", ctx.nuxt4, transparentNames),
    maskable: generatePwaImageType("PwaMaskableImage", ctx.nuxt4, maskableNames),
    favicon: generatePwaImageType("PwaFaviconImage", ctx.nuxt4, faviconNames),
    apple: generatePwaImageType("PwaAppleImage", ctx.nuxt4, appleNames),
    appleSplashScreen: generatePwaImageType("PwaAppleSplashScreenImage", ctx.nuxt4, appleSplashScreenNames)
  };
  if (nuxt.options.dev && nuxt.options.ssr) {
    sources.forEach((source) => nuxt.options.watch.push(source.replace(/\\/g, "/")));
  }
  return dts;
}
async function resolvePWAAssetsOptions(ctx) {
  const { options, nuxt } = ctx;
  if (!options.pwaAssets)
    return;
  const {
    disabled: useDisabled,
    config,
    preset,
    image,
    htmlPreset = "2023",
    overrideManifestIcons = false,
    includeHtmlHeadLinks = true,
    injectThemeColor = true,
    integration
  } = options.pwaAssets ?? {};
  const disabled = !(useDisabled === true) ? false : !config && !preset;
  let useImage;
  if (image) {
    useImage = await tryToResolveImage(ctx, image);
  } else {
    useImage = resolve(ctx.publicDirFolder, "favicon.svg");
  }
  useImage = relative(nuxt.options.srcDir, useImage);
  options.pwaAssets = {
    disabled,
    config: disabled || !config ? false : config,
    preset: disabled || config ? false : preset ?? "minimal-2023",
    image: useImage,
    htmlPreset,
    overrideManifestIcons,
    includeHtmlHeadLinks,
    injectThemeColor,
    integration
  };
  return {
    disabled,
    config: disabled || !config ? false : config,
    preset: disabled || config ? false : preset ?? "minimal-2023",
    images: [useImage],
    htmlPreset,
    overrideManifestIcons,
    includeHtmlHeadLinks,
    injectThemeColor,
    integration
  };
}
async function loadConfiguration(root, pwaAssets) {
  if (pwaAssets.config === false) {
    return await loadConfig(root, {
      config: false,
      preset: pwaAssets.preset,
      images: pwaAssets.images,
      logLevel: "silent"
    });
  }
  return await loadConfig(
    root,
    typeof pwaAssets.config === "boolean" ? root : { config: pwaAssets.config }
  );
}
async function checkFileExists(pathname) {
  try {
    await access(pathname, fs.constants.R_OK);
  } catch {
    return false;
  }
  return true;
}
async function tryToResolveImage(ctx, imageName) {
  for (const image of [
    // rootDir
    resolve(ctx.nuxt.options.rootDir, imageName),
    // srcDir
    resolve(ctx.nuxt.options.srcDir, imageName),
    // publicDir
    resolve(ctx.publicDirFolder, imageName)
  ]) {
    if (await checkFileExists(image))
      return image;
  }
  throw new Error(`PWA Assets image '${imageName}' cannot be resolved!`);
}

export { preparePWAIconTypes };
