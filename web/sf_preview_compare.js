// Frontend UI for SFPreviewCompare
// Adds left/right buttons to adjust the 'index' input parameter.

(function () {
  const NODE_TYPE = 'SFPreviewCompare';

  function addButtons(node, app) {
    if (node._sf_buttons_added) return;
    node._sf_buttons_added = true;

    const btnLeft = new LiteGraph.LGraphNode.makeButton?.('◀') || document.createElement('button');
    const btnRight = new LiteGraph.LGraphNode.makeButton?.('▶') || document.createElement('button');

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

    container.appendChild(left);
    container.appendChild(right);

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
      const onNodeCreated = nodeType.prototype.onNodeCreated;
      nodeType.prototype.onNodeCreated = function() {
        onNodeCreated?.apply(this, arguments);
        addButtons(this, appRef);
      };
    }
  });
})();
