import { defineComponent, h } from "#imports";
import { useApplePwaIcon } from "#pwa";
export default defineComponent({
  name: "PwaAppleImage",
  inheritAttrs: false,
  setup(_, { attrs = {} }) {
    const { icon } = useApplePwaIcon(attrs);
    return () => {
      const data = icon.value;
      if (!data)
        return;
      return h("img", data);
    };
  }
});
