(() => {
  if (window.__imageEditCaptureInstalled) {
    console.info("[image-edit-capture] already installed");
    return;
  }
  window.__imageEditCaptureInstalled = true;

  const matches = (url) => String(url || "").includes("/images/edits");
  const safeName = (value) =>
    String(value || "file").replace(/[^a-zA-Z0-9._-]+/g, "_");

  const download = (blob, name) => {
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = name;
    document.body.appendChild(link);
    link.click();
    setTimeout(() => {
      link.remove();
      URL.revokeObjectURL(url);
    }, 4000);
  };

  const inspectFormData = (body, transport) => {
    if (!(body instanceof FormData)) {
      console.info(`[image-edit-capture:${transport}] body is not FormData`);
      return;
    }

    let fileIndex = 0;
    for (const [field, value] of body.entries()) {
      if (!(value instanceof Blob)) {
        console.info(`[image-edit-capture:${transport}] field: ${field}`);
        continue;
      }

      const originalName = value.name || `${field}.bin`;
      const outputName = `${String(fileIndex).padStart(2, "0")}-${safeName(
        field
      )}-${safeName(originalName)}`;
      fileIndex += 1;
      download(value, outputName);
      console.info(
        `[image-edit-capture:${transport}] downloaded`,
        { field, name: outputName, type: value.type, size: value.size }
      );
    }
  };

  const originalFetch = window.fetch;
  window.fetch = function (input, init) {
    const url = typeof input === "string" ? input : input?.url;
    if (matches(url)) {
      if (init?.body) {
        inspectFormData(init.body, "fetch");
      } else if (input instanceof Request) {
        input
          .clone()
          .formData()
          .then((body) => inspectFormData(body, "fetch-request"))
          .catch((error) =>
            console.warn("[image-edit-capture] cannot read Request body", error)
          );
      }
    }
    return originalFetch.apply(this, arguments);
  };

  const originalOpen = XMLHttpRequest.prototype.open;
  const originalSend = XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.open = function (method, url) {
    this.__imageEditCaptureUrl = url;
    return originalOpen.apply(this, arguments);
  };
  XMLHttpRequest.prototype.send = function (body) {
    if (matches(this.__imageEditCaptureUrl)) {
      inspectFormData(body, "xhr");
    }
    return originalSend.apply(this, arguments);
  };

  console.info(
    "[image-edit-capture] installed; submit one image edit request"
  );
})();
