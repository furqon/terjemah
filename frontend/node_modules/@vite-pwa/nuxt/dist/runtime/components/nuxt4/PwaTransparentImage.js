import { defineComponent, h } from "#imports";
import { useTransparentPwaIcon } from "#pwa";
export default defineComponent({
  name: "PwaTransparentImage",
  inheritAttrs: false,
  setup(_, { attrs = {} }) {
    const { icon } = useTransparentPwaIcon(attrs);
    return () => {
      const data = icon.value;
      if (!data)
        return;
      return h("img", data);
    };
  }
});
