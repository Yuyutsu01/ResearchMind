/**
 * SelectionEngine for ResearchMind (Phase 6)
 * 
 * An independent, decoupled selection module reading browser-native window.getSelection()
 * and Range objects. Does NOT manipulate or override native browser highlights.
 */

export interface SelectionResult {
  text: string;
  range: Range | null;
  bounds: DOMRect | null;
  isCollapsed: boolean;
}

export class SelectionEngine {
  /**
   * Captures the current native browser selection.
   */
  public getSelection(): SelectionResult | null {
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed) return null;

    const text = sel.toString().trim();
    if (text.length < 2 || sel.rangeCount === 0) return null;

    const range = sel.getRangeAt(0);
    const bounds = range.getBoundingClientRect();

    return {
      text,
      range,
      bounds,
      isCollapsed: false,
    };
  }

  /**
   * Clears active browser text selection.
   */
  public clearSelection(): void {
    const sel = window.getSelection();
    if (sel) {
      sel.removeAllRanges();
    }
  }
}

export const selectionEngine = new SelectionEngine();
