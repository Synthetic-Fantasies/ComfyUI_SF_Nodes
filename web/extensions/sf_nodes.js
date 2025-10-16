// SF Nodes Web Extension
// Adds custom UI elements for better user experience

import { app } from "../../scripts/app.js";
import { ComfyWidgets } from "../../scripts/widgets.js";

// Custom reset button widget
function createResetButton(node, inputName, inputData, widgetName) {
    const widget = {
        type: "button",
        name: widgetName,
        size: [140, 30],
        draw: function (ctx, node, widgetWidth, y, widgetHeight) {
            const margin = 10;
            const buttonWidth = widgetWidth - margin * 2;
            const buttonHeight = widgetHeight - 4;

            // Button background
            ctx.fillStyle = "#ff6b6b";
            ctx.fillRect(margin, y + 2, buttonWidth, buttonHeight);

            // Button border
            ctx.strokeStyle = "#ff5252";
            ctx.lineWidth = 1;
            ctx.strokeRect(margin, y + 2, buttonWidth, buttonHeight);

            // Button text
            ctx.fillStyle = "#ffffff";
            ctx.font = "12px Arial";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillText("🔄 Reset", margin + buttonWidth / 2, y + buttonHeight / 2 + 2);
        },
        mouse: function (event, pos, node) {
            if (event.type === "pointerdown") {
                // Find the corresponding dropdown widget and set it to "reset"
                const resetWidget = node.widgets.find(w => w.name === inputName);
                if (resetWidget) {
                    resetWidget.value = "reset";
                    // Trigger node update
                    if (node.onResize) {
                        node.onResize(node.size);
                    }
                    app.graph.setDirtyCanvas(true);

                    // Reset back to "keep" after a short delay
                    setTimeout(() => {
                        resetWidget.value = "keep";
                        app.graph.setDirtyCanvas(true);
                    }, 100);
                }
                return true;
            }
            return false;
        }
    };

    return widget;
}

// Register custom widgets for SF nodes
app.registerExtension({
    name: "SF.CustomUI",

    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        // Add custom UI for SFOdometer
        if (nodeData.name === "SFOdometer") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const result = onNodeCreated?.apply(this, arguments);

                // Hide the reset dropdown
                const resetWidget = this.widgets.find(w => w.name === "reset_counter");
                if (resetWidget) {
                    resetWidget.type = "hidden";
                }

                // Add custom reset button
                const resetButton = createResetButton(this, "reset_counter", null, "reset_button");
                this.addCustomWidget(resetButton);

                return result;
            };
        }

        // Add custom UI for SFSequence
        if (nodeData.name === "SFSequence") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const result = onNodeCreated?.apply(this, arguments);

                // Hide the reset dropdown
                const resetWidget = this.widgets.find(w => w.name === "reset_sequence");
                if (resetWidget) {
                    resetWidget.type = "hidden";
                }

                // Add custom reset button
                const resetButton = createResetButton(this, "reset_sequence", null, "reset_button");
                this.addCustomWidget(resetButton);

                return result;
            };
        }

        // Add custom UI for SFTimer
        if (nodeData.name === "SFTimer") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const result = onNodeCreated?.apply(this, arguments);

                // Hide the reset dropdown
                const resetWidget = this.widgets.find(w => w.name === "reset_timer");
                if (resetWidget) {
                    resetWidget.type = "hidden";
                }

                // Add custom reset button
                const resetButton = createResetButton(this, "reset_timer", null, "reset_button");
                this.addCustomWidget(resetButton);

                return result;
            };
        }
    }
});

// Enhanced button styles and animations
const style = document.createElement('style');
style.textContent = `
    .sf-reset-button {
        background: linear-gradient(135deg, #ff6b6b, #ff5252);
        border: none;
        border-radius: 6px;
        color: white;
        padding: 8px 16px;
        font-size: 12px;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(255, 107, 107, 0.3);
    }
    
    .sf-reset-button:hover {
        background: linear-gradient(135deg, #ff5252, #ff4444);
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(255, 107, 107, 0.4);
    }
    
    .sf-reset-button:active {
        transform: translateY(0);
        box-shadow: 0 2px 4px rgba(255, 107, 107, 0.3);
    }
    
    .sf-reset-button::before {
        content: "🔄 ";
        margin-right: 4px;
    }
`;
document.head.appendChild(style);