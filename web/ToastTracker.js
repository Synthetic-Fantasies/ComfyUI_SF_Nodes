import { SFToast } from "./utils.js";

export class ToastTracker {
  constructor() {
    this.toastCounts = new Map();
  }

  /**
   * Show a toast message with tracking by key
   * @param {string} key - Unique key to track this toast type
   * @param {string} type - Toast type (info, warning, error, etc.)
   * @param {string} message - Toast message
   * @param {number} maxShows - Maximum number of times to show this toast
   * @returns {boolean} True if toast was shown, false if max limit reached
   */
  showToast(key, type, message, maxShows = 2) {
    const currentCount = this.toastCounts.get(key) || 0;
    
    if (currentCount >= maxShows) {
      return false;
    }

    SFToast(type, message);
    this.toastCounts.set(key, currentCount + 1);
    return true;
  }

  /**
   * Reset the count for a specific key
   * @param {string} key - Key to reset
   */
  resetKey(key) {
    this.toastCounts.delete(key);
  }

  /**
   * Reset all toast counts
   */
  resetAll() {
    this.toastCounts.clear();
  }

  /**
   * Get the current count for a key
   * @param {string} key - Key to check
   * @returns {number} Current count for the key
   */
  getCount(key) {
    return this.toastCounts.get(key) || 0;
  }

  /**
   * Check if a key has reached its maximum
   * @param {string} key - Key to check
   * @param {number} maxShows - Maximum number of shows
   * @returns {boolean} True if max reached, false otherwise
   */
  hasReachedMax(key, maxShows = 2) {
    return this.getCount(key) >= maxShows;
  }
}
