import { defineComponent, h } from "#imports";
import { useAppleSplashScreenPwaIcon } from "#pwa";
export default defineComponent({
  name: "PwaAppleImage",
  inheritAttrs: false,
  setup(_, { attrs = {} }) {
    const { icon } = useAppleSplashScreenPwaIcon(attrs);
    return () => {
      const data = icon.value;
      if (!data)
        return;
      return h("img", data);
    };
  }
});
