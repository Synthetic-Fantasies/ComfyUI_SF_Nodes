import { SFToast } from "./utils.js";

export class ToastTracker {
  static DEFAULT_MAX_SHOWS = 2;

  constructor() {
    this.toastCounts = new Map();
    this.maxShows = new Map();
  }

  /**
   * Show a toast message with tracking by key
   * @param {string} key - Unique key to track this toast type
   * @param {string} type - Toast type (info, warning, error, etc.)
   * @param {string} message - Toast message
   * @param {number} maxShows - Maximum number of times to show this toast (overrides stored max if provided)
   * @returns {boolean} True if toast was shown, false if max limit reached
   */
  showToast(key, type, message, maxShows = null) {
    // Get current count and max, setting max if provided
    let currentCount, storedMax = this.getCountAndMax(key, maxShows);
    
    if (currentCount >= storedMax) {
      return false;
    }

    SFToast(type, message);
    this.incrementCount(key);
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
   * Reset the count and max for a specific key
   * @param {string} key - Key to reset
   */
  resetKeyAndMax(key) {
    this.toastCounts.delete(key);
    this.maxShows.delete(key);
  }

  /**
   * Reset all toast counts
   */
  resetAll() {
    this.toastCounts.clear();
  }

  /**
   * Reset all toast counts and max values
   */
  resetAllAndMax() {
    this.toastCounts.clear();
    this.maxShows.clear();
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
   * Get current count and max for a key, setting max if provided
   * @param {string} key - Key to check
   * @param {number|null} maxShows - Max to set if provided
   * @returns {[number, number]} Tuple of [currentCount, storedMax]
   */
  getCountAndMax(key, maxShows = null) {
    // If maxShows is provided, update the stored max for this key
    if (maxShows !== null) {
      this.maxShows.set(key, maxShows);
    }
    else{
      maxShows =  this.maxShows.get(key)
      if (maxShows === undefined) {
        maxShows = ToastTracker.DEFAULT_MAX_SHOWS;
        this.maxShows.set(key, maxShows);
      }
    }
    let currentCount = this.toastCounts.get(key);
    if (currentCount === undefined) {
      currentCount = 0;
      this.toastCounts.set(key, currentCount);
    }
    return (currentCount, maxShows);
  }

  /**
   * Increment the count for a key
   * @param {string} key - Key to increment
   */
  incrementCount(key) {
    const currentCount = this.toastCounts.get(key) || 0;
    this.toastCounts.set(key, currentCount + 1);
  }

  /**
   * Get the stored max for a key
   * @param {string} key - Key to check
   * @returns {number} Stored max value or DEFAULT_MAX_SHOWS if not set
   */
  getMax(key) {
    return this.maxShows.get(key) || ToastTracker.DEFAULT_MAX_SHOWS;
  }

  /**
   * Set the max for a key
   * @param {string} key - Key to set max for
   * @param {number} maxShows - Maximum number of shows
   */
  setMax(key, maxShows) {
    this.maxShows.set(key, maxShows);
  }

  /**
   * Check if a key has reached its maximum
   * @param {string} key - Key to check
   * @returns {boolean} True if max reached, false otherwise
   */
  hasReachedMax(key) {
    const storedMax = this.getMax(key);
    return this.getCount(key) >= storedMax;
  }
}
