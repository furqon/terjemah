import { defineComponent, h } from "#imports";
import { useMaskablePwaIcon } from "#pwa";
export default defineComponent({
  name: "PwaMaskableImage",
  inheritAttrs: false,
  setup(_, { attrs = {} }) {
    const { icon } = useMaskablePwaIcon(attrs);
    return () => {
      const data = icon.value;
      if (!data)
        return;
      return h("img", data);
    };
  }
});
