/**
 * TextLayerManager for ResearchMind
 * 
 * Manages PDF.js native text layer rendering, CSS custom property assignment (--scale-factor),
 * and DOM node stabilization to prevent innerHTML destruction during scroll events.
 */

export class TextLayerManager {
  private activeTasks: Map<number, any> = new Map();
  private renderedPages: Set<number> = new Set();

  /**
   * Sets the required --scale-factor CSS custom property on the .textLayer container.
   */
  public setScaleFactor(container: HTMLElement, scale: number): void {
    container.style.setProperty("--scale-factor", scale.toString());
  }

  /**
   * Renders the native PDF.js text layer into the container element.
   * Ensures DOM nodes are created cleanly and assigned exact scale variables.
   */
  public async renderTextLayer(
    pageNumber: number,
    page: any,
    viewport: any,
    scale: number,
    container: HTMLElement
  ): Promise<void> {
    // Cancel any in-flight text layer rendering task for this page
    if (this.activeTasks.has(pageNumber)) {
      try {
        const existingTask = this.activeTasks.get(pageNumber);
        if (existingTask && existingTask.cancel) {
          existingTask.cancel();
        }
      } catch (err) {
        // Ignore cancellation errors
      }
      this.activeTasks.delete(pageNumber);
    }

    // Set --scale-factor CSS variable
    this.setScaleFactor(container, scale);

    // Fetch text content
    const textContent = await page.getTextContent();
    
    // Clear container only before a fresh render task begins
    container.innerHTML = "";

    const pdfjsLib = (window as any).pdfjsLib;
    if (!pdfjsLib || !pdfjsLib.renderTextLayer) {
      console.warn("PDF.js renderTextLayer not available");
      return;
    }

    // Render using official PDF.js renderTextLayer API
    const renderTask = pdfjsLib.renderTextLayer({
      textContentSource: textContent,
      container,
      viewport,
      textDivs: [],
      enhanceTextSelection: true,
    });

    this.activeTasks.set(pageNumber, renderTask);

    try {
      if (renderTask && renderTask.promise) {
        await renderTask.promise;
      }
      this.renderedPages.add(pageNumber);
    } catch (err: any) {
      if (err?.name !== "RenderingCancelledException") {
        console.error(`Error rendering text layer for page ${pageNumber}`, err);
      }
    } finally {
      this.activeTasks.delete(pageNumber);
    }
  }

  /**
   * Checks whether a page has already been rendered with text layer DOM nodes.
   */
  public isPageRendered(pageNumber: number): boolean {
    return this.renderedPages.has(pageNumber);
  }

  /**
   * Invalidates rendered page cache (e.g. when zoom changes).
   */
  public invalidateCache(): void {
    this.renderedPages.clear();
    this.activeTasks.forEach((task) => {
      if (task && task.cancel) {
        try {
          task.cancel();
        } catch (e) {}
      }
    });
    this.activeTasks.clear();
  }
}

export const textLayerManager = new TextLayerManager();
