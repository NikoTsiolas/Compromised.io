// The suite's `test`, plus `offline()`: every spec file calls it once at its top, so that every
// request not for the app itself is answered locally (see images.ts) and no test ever contacts
// a publisher. It is a call, not a hook registered when this module loads, because a module is
// loaded once per worker and its hooks would then cover only the first spec file.
import { test } from "@playwright/test";

import { servePublisherImages } from "./images";

export function offline() {
  test.beforeEach(async ({ page }) => {
    await servePublisherImages(page);
  });
}

export { test };
export { expect, type Page } from "@playwright/test";
