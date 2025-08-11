import { SFConsoleLog } from "./Utils.js";

export class ImageHistoryTracker {
  constructor(maxImages = 16) {
    this.imagesTracked = [];
    this.MAX_IMAGES = maxImages;
  }

  /**
   * Add a new image to the tracking history
   * @param {HTMLImageElement} newImage - The image to add
   * @returns {HTMLImageElement[]} The updated images array
   */
  pushToImgs(newImage) {
    // Check if image is undefined or null
    if (!newImage || !newImage.naturalWidth) {
      SFConsoleLog("Undefined or null image, skipping");
      return this.imagesTracked;
    }

    const imageExists = this.imagesTracked.some((img) => {
      // Extract filename from URLs by removing the random parameter
      const getFilename = (url) => {
        if (!url) return "";
        const match = url.match(/filename=([^&]+)/);
        return match ? match[1] : "";
      };

      const newImageFilename = getFilename(newImage.src);
      const existingImageFilename = getFilename(img.src);

      return newImageFilename === existingImageFilename;
    });

    if (imageExists) {
      SFConsoleLog("Image already exists, skipping");
      return this.imagesTracked;
    }

    this.imagesTracked.push(newImage);
    // If array exceeds MAX_IMAGES, remove oldest image(s)
    if (this.imagesTracked.length > this.MAX_IMAGES) {
      this.imagesTracked.shift(); // removes first (oldest) element
    }
    SFConsoleLog("imagesTracked list updated, length:", this.imagesTracked.length);
    return this.imagesTracked;
  }

  /**
   * Get the current images array
   * @returns {HTMLImageElement[]} The tracked images
   */
  getImages() {
    return this.imagesTracked;
  }

  /**
   * Get the number of tracked images
   * @returns {number} The count of tracked images
   */
  getImageCount() {
    return this.imagesTracked.length;
  }

  /**
   * Get the last image in the history
   * @returns {HTMLImageElement|null} The last image or null if empty
   */
  getLastImage() {
    return this.imagesTracked.length > 0 ? this.imagesTracked[this.imagesTracked.length - 1] : null;
  }

  /**
   * Get the second to last image in the history
   * @returns {HTMLImageElement|null} The second to last image or null if not available
   */
  getSecondToLastImage() {
    return this.imagesTracked.length > 1 ? this.imagesTracked[this.imagesTracked.length - 2] : null;
  }

  /**
   * Get the last two images from history
   * @returns {HTMLImageElement[]} Array containing the last two images
   */
  getLastTwoImages() {
    return this.imagesTracked.slice(-2);
  }

  /**
   * Check if an image exists in the tracking history
   * @param {HTMLImageElement} image - The image to check
   * @returns {boolean} True if the image exists in history
   */
  hasImage(image) {
    return this.imagesTracked.some((img) => img === image);
  }

  /**
   * Clear all tracked images
   */
  clear() {
    this.imagesTracked = [];
  }

  /**
   * Check if there are enough images for comparison (at least 2)
   * @returns {boolean} True if there are at least 2 images
   */
  hasEnoughImagesForComparison() {
    return this.imagesTracked.length > 1;
  }

  /**
   * Check if there are any tracked images
   * @returns {boolean} True if there are any images
   */
  hasAnyImages() {
    return this.imagesTracked.length > 0;
  }
}
