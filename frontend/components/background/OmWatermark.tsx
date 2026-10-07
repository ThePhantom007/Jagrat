import {OM_PATH, OM_VIEWBOX} from "./om-path";

/** Large, translucent Om centred behind page content. Decorative only. */
export function OmWatermark() {
  return (
    <svg className="jg-om" viewBox={OM_VIEWBOX} aria-hidden="true" focusable="false">
      <path d={OM_PATH} />
    </svg>
  );
}
