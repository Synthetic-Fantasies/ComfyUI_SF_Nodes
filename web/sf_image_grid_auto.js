// Frontend UI for SFImageGridAuto
// Ensures an image preview widget is present and displays the rendered grid inside the node.

(function () {
  const NODE_TYPE = 'SFImageGridAuto';

  function ensureImageWidget(node, app) {
    try {
      const CW = (app?.ui && app.ui.comfyWidgets) || window.ComfyWidgets || window.app?.ui?.comfyWidgets;
      if (CW && typeof CW.IMAGE === 'function') {
        CW.IMAGE(node, 'image', app);
      } else if (!node.widgets?.some?.(w => w.type === 'image' || w.name === 'image')) {
        node.addWidget?.('image', 'image', null, null, { serialize: false });
      }
    } catch (e) {
      // ignore
    }
  }

  async function setWidgetFromMessage(node, app, message) {
    try {
      const widget = node.widgets?.find?.(w => w.type === 'image' || w.name === 'image');
      if (!widget) return;
      const ref = message?.images?.[0] || message?.image || (message?.result?.[0]?.[0]);
      if (!ref || !app?.api?.getImage) return;
      const blob = await app.api.getImage(ref);
      const url = URL.createObjectURL(blob);
      const img = new Image();
      img.onload = () => {
        URL.revokeObjectURL(url);
        widget.value = img;
        node.img = img;
        node.setDirtyCanvas(true, true);
      };
      img.src = url;
    } catch (e) {
      // ignore
    }
  }

  function drawBackground(nodeType) {
    const prev = nodeType.prototype.onDrawBackground;
    nodeType.prototype.onDrawBackground = function(ctx) {
      prev?.apply(this, arguments);
      try {
        const imgWidget = this.widgets?.find?.(w => w.type === 'image' || w.name === 'image');
        const tex = this.bgImage || this.img || imgWidget?.value;
        if (!tex) return;
        const w = this.size[0] - 10;
        const h = this.size[1] - 20;
        const x = 5, y = 5;
        ctx.drawImage(tex, 0, 0, tex.width, tex.height, x, y, w, h);
      } catch (e) {
        // ignore
      }
    };
  }

  app.registerExtension?.({
    name: 'sf.grid.auto',
    async beforeRegisterNodeDef(nodeType, nodeData, appRef) {
      if (nodeData?.name !== NODE_TYPE) return;
      try { console.debug('[SFImageGridAuto] extension active'); } catch (e) {}
      const onNodeCreated = nodeType.prototype.onNodeCreated;
      nodeType.prototype.onNodeCreated = function() {
        onNodeCreated?.apply(this, arguments);
        ensureImageWidget(this, appRef);
      };
      drawBackground(nodeType);
      const prevOnExecuted = nodeType.prototype.onExecuted;
      nodeType.prototype.onExecuted = async function(message) {
        await setWidgetFromMessage(this, appRef, message);
        return prevOnExecuted?.apply(this, arguments);
      };
    }
    ,
    async nodeCreated(node, appRef) {
      try {
        if (node?.comfyClass === NODE_TYPE) {
          ensureImageWidget(node, appRef);
        }
      } catch (e) {}
    }
  });
})();


