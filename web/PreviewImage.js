import { app } from "/scripts/app.js";
import { BaseSmartWidget, BaseSmartWidgetManager } from "./widgets/BaseSmartWidget.js";
import { SmartButton } from "./widgets/SmartButton.js";
import { Shapes, SFToast } from "./Utils.js";
import { ImageHistoryTracker } from "./ImageHistoryTracker.js";
import { ToastTracker } from "./ToastTracker.js";



NODE_NAME="SFPreviewImage";

app.registerExtension({
  name: "SF.PreviewImage",
  async beforeRegisterNodeDef(nodeType, nodeData, app) {
    if (nodeData.name === NODE_NAME) {
    }
  },
  async nodeCreated(node) {
    if (node.comfyClass !== NODE_NAME) {
      return;
    }

    // init size
    node.size = [285, 330];

    SFConsoleLog("node", node);

    // vars
    let a = null;
    let b = null;
    let c = null;
    let compare = false;
    const imageTracker = new ImageHistoryTracker(16);

    let mouse = {
      mouseInNode: false,
      x: 0,
      y: 0,
    };

    // other vars
    const toastTracker = new ToastTracker();



    function cycleImgs() {
      if (imageTracker.getImageCount() === 1) {
        toastTracker.showToast("cycleImgs", "info", "Only this image exist in this node history");
        return;
      }

      // Switch to previous imagesTracked if available
      if (node.imgs && imageTracker.getImageCount() > 1) {
        node.imgs = imageTracker.getImages(); // Show previous image
      }
    }

    function togglingLastTwoImages() {
      SFConsoleLog("imagesTracked", imageTracker.getImages());
      // Only cycle between last two imagesTracked
      if (imageTracker.hasEnoughImagesForComparison()) {
        node.imageIndex = 0;

        // Get current image
        const currentImg = node.imgs[0];

        // Get last two imagesTracked from history
        const lastTwo = imageTracker.getLastTwoImages();

        // If current is last image, show second to last
        // If current is second to last, show last
        const nextImg = currentImg === lastTwo[1] ? lastTwo[0] : lastTwo[1];

        // Update display
        node.imgs = [nextImg];

        // Update button text with underline using Unicode
        const isShowingCurrent = nextImg === lastTwo[1];
        b.text = isShowingCurrent ? "[Current] | Previous" : "Current | [Previous]";

        SFConsoleLog("Toggling between last two imagesTracked");
      } else {
        toastTracker.showToast("togglingLastTwo", "info", "You must execute this node at least twice");
      }
    }

    function toggleButtonActivation() {
      c.isActive = compare;
      if (!compare) {
        c.color = c.originalColor;
        c.textColor = c.originalTextColor;
      } else {
        c.color = "#80a1c0";
        c.textColor = "black";
      }
    }

    function showButtons() {
      a.isVisible = true;
      b.isVisible = true;
      // c.isVisible = true;
    }

    function createButtons(startVisible = true) {
      a = new SmartButton(75, 8, 55, 20, node, "History");
      a.allowVisualHover = true;
      a.textYoffset = -0;
      a.isVisible = startVisible;
      a.shape = Shapes.ROUND_L;
      a.roundRadius = 5;
      a.outlineWidth = 1;
      a.outlineColor = "#656565";
      a.color = "#222222";
      a.font = "12px Arial";
      a.onClick = () => {
        if (compare) {
          // cancel compare
          compare = !compare;
          toggleButtonActivation(c, compare);
        }
        if (!imageTracker.hasAnyImages()) {
          toastTracker.showToast("noImages", "info", "No images in this node history");
          return;
        }
        if (imageTracker.hasEnoughImagesForComparison()) {
          togglingLastTwoImages();
        } else {
          cycleImgs();
        }
      };

      b = new SmartButton(75 + 55, 8, 120, 20, node, "[Current] | Previous");
      b.allowVisualHover = true;
      b.textYoffset = -0;
      b.isVisible = startVisible;
      b.shape = Shapes.ROUND_R;
      b.roundRadius = 5;
      b.outlineWidth = 1;
      b.outlineColor = "#656565";
      b.color = "#222222";
      b.font = "12px Arial";
      b.onClick = () => {
        if (compare) {
          // cancel compare
          compare = !compare;
          toggleButtonActivation(c, compare);
        }
        togglingLastTwoImages();
      };

      c = new SmartButton(75 + 55 + 125, 8 + 1, 18, 20, node, "|");
      c.allowVisualHover = true;
      c.textYoffset = -0.05;
      c.isVisible = startVisible;
      c.shape = Shapes.CIRCLE;
      //c.roundRadius = 5;
      c.outlineWidth = 1;
      c.outlineColor = "#656565";
      c.color = "#222222";
      c.activeColor = c.font = "12px Arial";
      c.onClick = () => {
        // reset togglingLastTwoImages
        if (b.text !== "[Current] | Previous") togglingLastTwoImages();

        // reset from history state
        if (node.imageIndex === null) {
          if (imageTracker.hasEnoughImagesForComparison()) {
            node.imageIndex = 0; // reset to single view
            node.imgs = node.imgs = [node.imgs[node.imgs.length - 1]]; // show last image in node.imgs list;
          }
        }

        // start compare
        if (!imageTracker.hasEnoughImagesForComparison()) {
          toastTracker.showToast("compareMode", "info", "You must execute this node at least twice");
          return;
        }
        compare = !compare;
        toggleButtonActivation(c, compare);
      };
    }

    createButtons();

    node.onExecuted = async function (message) {
      // Wait for image to be loaded
      for (let i = 0; i < 20 && !node.imgs; i++) {
        SFConsoleLog("wait..", i);
        await new Promise((resolve) => setTimeout(resolve, 100));
      }
      if (!node.imgs) return;

      showButtons();

      // Reset togglingLastTwoImages
      if (b.text !== "[Current] | Previous") togglingLastTwoImages();
      node.setDirtyCanvas(true, false);

      setTimeout(() => {
        // push last image
        const lastImage = node.imgs?.at(-1);
        imageTracker.pushToImgs(lastImage);

        // Override draw function in ImagePreviewWidget
        const previewWidget = node.widgets.find((widget) => !(widget instanceof BaseSmartWidget));
        if (!previewWidget) {
          SFConsoleLog("ImagePreviewWidget not found");
          return;
        }
    
        const originalDraw = previewWidget.drawWidget;
        if (originalDraw) {
          previewWidget.draw = function (ctx, node, widget_width, y, widget_height, ...args) {
            // Call the original draw function first
            originalDraw.apply(this, [ctx, node, widget_width, y, widget_height, ...args]);
            
            drawImgOverlay(mouse, node, widget_width, y, ctx, imageTracker.getImages(), compare);
          };
        }
      }, 300);
    };

    node.onResize = function (newSize) {
      // limit width size while resizing
      node.size[0] = Math.max(285, newSize[0]);
      // SFConsoleLog("Node", node);
    };

    const m = new BaseSmartWidgetManager(node, NODE_NAME);
    const origOnRemoved = node.onRemoved;
    node.onRemoved = function () {
      origOnRemoved?.apply(this, arguments);
      m.destroy();
    };

    node.onMouseEnter = (e) => {
      SFConsoleLog('node.y',node.y);
      mouse.mouseInNode = true;
    };

    node.onMouseLeave = (e) => {

      mouse.mouseInNode = false;
    };

    node.onMouseMove = (e, pos) => {
      if (mouse.mouseInNode) {
        const graphMouse = app.canvas.graph_mouse;
        mouse.x = graphMouse[0] - node.pos[0];
        mouse.y = graphMouse[1] - node.pos[1];
      }
    };
  },
  
});

function drawImgOverlay(mouse, node, widget_width, y, ctx, _imagesRef, compareMode = false) {
  if (!compareMode) return;
  y = y ? y : 0; // Ensure y is defined

  const allowImageSizeDraw = app.extensionManager.setting.get("Comfy.Node.AllowImageSizeDraw", true);
  const IMAGE_TEXT_SIZE_TEXT_HEIGHT = allowImageSizeDraw ? 15 : 0;

  const img2 = _imagesRef[0];
  const img1 = _imagesRef.length > 1 ? _imagesRef[_imagesRef.length - 2] : null;
  if (!img2) {
    SFConsoleLog("No previous image to compare with");
    return;
  };

  const dw = widget_width;
  const dh = node.size[1] - y - IMAGE_TEXT_SIZE_TEXT_HEIGHT;
  let w = Math.max(img1.naturalWidth, img2.naturalWidth);
  let h = Math.max(img1.naturalHeight, img2.naturalHeight);

  const scaleX = dw / w;
  const scaleY = dh / h;
  const scale = Math.min(scaleX, scaleY, 1);

  w *= scale;
  h *= scale;

  // Centered position within the widget
  const imgX = (dw - w) / 2;
  const imgY = (dh - h) / 2 + y; // +y to offset within canvas

  const mouseX = mouse.x
  const splitX = Math.max(imgX, Math.min(mouseX, imgX + w));
  const splitRatio = (splitX - imgX) / w;

  if (img1 && compareMode) {
   ctx.drawImage(img1, 0, 0, img1.naturalWidth * splitRatio, img1.naturalHeight, imgX, imgY, w * splitRatio, h);
  }
}