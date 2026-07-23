/**
 * Virtual PageCache for ResearchMind (Phase 5)
 * 
 * Maintains active page ± 2 surrounding pages mounted in memory during scroll.
 * Prevents active text selections from collapsing when scrolling across page bounds.
 */

export class PageCache {
  private bufferSize: number = 2; // Keep current page ± 2 pages in memory

  /**
   * Calculates the set of visible/buffered page numbers for a given current page.
   */
  public getBufferedPages(currentPage: number, totalPages: number): Set<number> {
    const pages = new Set<number>();
    const start = Math.max(1, currentPage - this.bufferSize);
    const end = Math.min(totalPages, currentPage + this.bufferSize);

    for (let p = start; p <= end; p++) {
      pages.add(p);
    }
    return pages;
  }

  /**
   * Determines if a target page number should be mounted in DOM.
   */
  public isPageMounted(pageNum: number, currentPage: number, totalPages: number): boolean {
    const minPage = Math.max(1, currentPage - this.bufferSize);
    const maxPage = Math.min(totalPages, currentPage + this.bufferSize);
    return pageNum >= minPage && pageNum <= maxPage;
  }
}

export const pageCache = new PageCache();
