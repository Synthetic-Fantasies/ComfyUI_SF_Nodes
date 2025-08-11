// Frontend UI for SFPreviewCompare
// Adds left/right buttons to adjust 'index' and a mode switcher (A/B/Swipe/Area) at display time.

(function () {
  const NODE_TYPE = 'SFPreviewCompare';

  function addButtons(node, app) {
    if (node._sf_buttons_added) return;
    node._sf_buttons_added = true;

    const MODES = ['A', 'B', 'Swipe', 'Area'];
    node._sf_mode = node._sf_mode || 'Swipe';

    function setIndex(delta) {
      const idxSlot = node.inputs?.findIndex(i => i && i.name === 'index');
      if (idxSlot == null || idxSlot < 0) return;
      let current = node.widgets?.find?.(w => w.name === 'index')?.value;
      if (typeof current !== 'number') current = 0;
      const next = current + delta;
      const widget = node.widgets?.find?.(w => w.name === 'index');
      if (widget) {
        widget.value = next;
        if (widget.callback) widget.callback(next, app);
        node.setDirtyCanvas(true, true);
      }
    }

    // Fallback simple HTML buttons
    const container = document.createElement('div');
    container.style.display = 'flex';
    container.style.gap = '4px';
    container.style.justifyContent = 'center';
    container.style.margin = '4px 0';

    const left = document.createElement('button');
    left.textContent = '◀';
    left.onclick = () => setIndex(-1);

    const right = document.createElement('button');
    right.textContent = '▶';
    right.onclick = () => setIndex(+1);

    const mode = document.createElement('select');
    for (const m of MODES) {
      const opt = document.createElement('option');
      opt.value = m;
      opt.textContent = m;
      if (m === node._sf_mode) opt.selected = true;
      mode.appendChild(opt);
    }
    mode.onchange = () => {
      node._sf_mode = mode.value;
      node.setDirtyCanvas(true, true);
    };

    container.appendChild(left);
    container.appendChild(right);
    container.appendChild(mode);

    // Ensure an image widget exists and is wired to execution results
    try {
      const CW = (app?.ui && app.ui.comfyWidgets) || window.ComfyWidgets || window.app?.ui?.comfyWidgets;
      if (CW && typeof CW.IMAGE === 'function') {
        // Adds a non-serialized image preview widget bound to output name 'image'
        CW.IMAGE(node, 'image', app);
      } else if (!node.widgets?.some?.(w => w.type === 'image' || w.name === 'image')) {
        // Fallback: minimal image widget (value set in onExecuted)
        node.addWidget?.('image', 'image', null, null, { serialize: false });
      }
    } catch (e) {
      // ignore
    }

    // Update image widget on execution
    const prevOnExecuted = node.onExecuted;
    node.onExecuted = async function(message) {
      try {
        const widget = this.widgets?.find?.(w => w.type === 'image' || w.name === 'image');
        const first = message?.images?.[0];
        if (widget && first && app?.api?.getImage) {
          const blob = await app.api.getImage(first);
          const url = URL.createObjectURL(blob);
          const img = new Image();
          img.onload = () => {
            URL.revokeObjectURL(url);
            widget.value = img;
            this.img = img; // allow background draw fallbacks
            this.setDirtyCanvas(true, true);
          };
          img.src = url;
        }
      } catch (e) {
        // ignore
      }
      return prevOnExecuted?.apply(this, arguments);
    };

    const onDrawForeground = node.onDrawForeground;
    node.onDrawForeground = function(ctx) {
      onDrawForeground?.call(this, ctx);
      if (!this._sf_btn_container) {
        this._sf_btn_container = container;
        const root = app?.canvas?.parentNode || document.body;
        root.appendChild(container);
      }
      const pos = this.getAbsolutePosition();
      container.style.position = 'absolute';
      container.style.left = (pos[0] + 10) + 'px';
      container.style.top = (pos[1] + this.size[1] - 24) + 'px';
    };

    const onRemoved = node.onRemoved;
    node.onRemoved = function() {
      onRemoved?.call(this);
      if (this._sf_btn_container && this._sf_btn_container.parentNode) {
        this._sf_btn_container.parentNode.removeChild(this._sf_btn_container);
        this._sf_btn_container = null;
      }
    };
  }

  app.registerExtension?.({
    name: 'sf.preview.compare',
    async beforeRegisterNodeDef(nodeType, nodeData, appRef) {
      if (nodeData?.name !== NODE_TYPE) return;
      try { console.debug('[SFPreviewCompare] extension active'); } catch (e) {}
      const onNodeCreated = nodeType.prototype.onNodeCreated;
      nodeType.prototype.onNodeCreated = function() {
        onNodeCreated?.apply(this, arguments);
        addButtons(this, appRef);
      };
      // Override onDrawBackground to visualize chosen mode using the combined output
      const onDrawBackground = nodeType.prototype.onDrawBackground;
      nodeType.prototype.onDrawBackground = function(ctx) {
        onDrawBackground?.apply(this, arguments);
        try {
          const imgWidget = this.widgets?.find?.(w => w.type === 'image' || w.name === 'image');
          const tex = this.bgImage || this.img || imgWidget?.value;
          if (!tex) return;
          const mode = this._sf_mode || 'Swipe';
          const w = this.size[0] - 10;
          const h = this.size[1] - 40;
          const x = 5, y = 5;
          if (mode === 'A' || mode === 'B') {
            // Assume combined is [A|B]; crop left or right half
            const sx = (mode === 'A') ? 0 : tex.width / 2;
            const sw = tex.width / 2;
            ctx.drawImage(tex, sx, 0, sw, tex.height, x, y, w, h);
          } else if (mode === 'Swipe') {
            const swipeX = Math.floor((Date.now() / 20) % w);
            const sw = tex.width / 2;
            // left area from A
            ctx.drawImage(tex, 0, 0, sw, tex.height, x, y, swipeX, h);
            // right area from B
            const remain = w - swipeX;
            if (remain > 0)
              ctx.drawImage(tex, sw, 0, sw, tex.height, x + swipeX, y, remain, h);
          } else if (mode === 'Area') {
            const sw = tex.width / 2;
            // draw A as base
            ctx.drawImage(tex, 0, 0, sw, tex.height, x, y, w, h);
            // overlay B with transparency
            ctx.save();
            ctx.globalAlpha = 0.5;
            ctx.drawImage(tex, sw, 0, sw, tex.height, x, y, w, h);
            ctx.restore();
          }
        } catch (e) {
          // ignore draw errors
        }
      };
      // Ensure widget exists and populate on execution if ComfyWidgets didn't
      const prevOnExecuted = nodeType.prototype.onExecuted;
      nodeType.prototype.onExecuted = async function(message) {
        try {
          const widget = this.widgets?.find?.(w => w.type === 'image' || w.name === 'image');
          if (widget && !widget.value) {
            // Try multiple known shapes
            const ref = message?.images?.[0] || message?.image || (message?.result?.[0]?.[0]);
            if (ref && appRef?.api?.getImage) {
              const blob = await appRef.api.getImage(ref);
              const url = URL.createObjectURL(blob);
              const img = new Image();
              img.onload = () => {
                URL.revokeObjectURL(url);
                widget.value = img;
                this.img = img;
                this.setDirtyCanvas(true, true);
              };
              img.src = url;
            }
          }
        } catch (e) {}
        return prevOnExecuted?.apply(this, arguments);
      };
    }
  });
})();
