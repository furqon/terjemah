import { defineComponent, h } from "#imports";
import { useFaviconPwaIcon } from "#pwa";
export default defineComponent({
  name: "PwaFaviconImage",
  inheritAttrs: false,
  setup(_, { attrs = {} }) {
    const { icon } = useFaviconPwaIcon(attrs);
    return () => {
      const data = icon.value;
      if (!data)
        return;
      return h("img", data);
    };
  }
});
