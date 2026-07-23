/**
 * RBush-powered Spatial Document Index for ResearchMind
 * 
 * Uses high-performance 2D R-Tree spatial indexing via RBush for instant (< 1ms)
 * hit-testing, point lookups, and bounding-box queries over non-text PDF objects
 * (equations, figures, tables, charts).
 */

import RBush from "rbush";
import { DocumentObject, BoundingBox } from "./document_model";

// Extended RBush Item Interface
export interface SpatialItem {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
  page: number;
  object: DocumentObject;
}

export class SpatialDocumentIndex {
  private tree: RBush<SpatialItem> = new RBush<SpatialItem>();
  private pageItems: Map<number, SpatialItem[]> = new Map();

  /**
   * Resets and clears the spatial R-Tree index.
   */
  public clear(): void {
    this.tree.clear();
    this.pageItems.clear();
  }

  /**
   * Bulk loads semantic document objects into the RBush spatial R-tree.
   */
  public loadObjects(objects: DocumentObject[]): void {
    this.clear();
    const items: SpatialItem[] = [];

    for (const obj of objects) {
      if (!obj.bounding_box || obj.bounding_box.length < 4) continue;
      const [x0, y0, x1, y1] = obj.bounding_box;
      const page = obj.page || 1;

      const item: SpatialItem = {
        minX: Math.min(x0, x1),
        minY: Math.min(y0, y1),
        maxX: Math.max(x0, x1),
        maxY: Math.max(y0, y1),
        page,
        object: obj,
      };

      items.push(item);

      if (!this.pageItems.has(page)) {
        this.pageItems.set(page, []);
      }
      this.pageItems.get(page)!.push(item);
    }

    // High-performance bulk load into RBush R-Tree
    if (items.length > 0) {
      this.tree.load(items);
    }
  }

  /**
   * Performs hit-testing at point (x, y) on a given page in < 1ms using RBush.
   */
  public hitTestPoint(page: number, x: number, y: number): DocumentObject | null {
    const candidates = this.tree.search({
      minX: x,
      minY: y,
      maxX: x,
      maxY: y,
    });

    const pageMatches = candidates.filter((item) => item.page === page);
    if (pageMatches.length === 0) return null;

    // Return most specific/topmost matching object
    return pageMatches[pageMatches.length - 1].object;
  }

  /**
   * Spatial bounding box search using RBush R-Tree intersection query.
   */
  public searchRange(page: number, bbox: BoundingBox): DocumentObject[] {
    const candidates = this.tree.search({
      minX: Math.min(bbox.x0, bbox.x1),
      minY: Math.min(bbox.y0, bbox.y1),
      maxX: Math.max(bbox.x0, bbox.x1),
      maxY: Math.max(bbox.y0, bbox.y1),
    });

    return candidates
      .filter((item) => item.page === page)
      .map((item) => item.object);
  }

  /**
   * Maps a native DOM text selection bounding box to the best matching semantic document object.
   */
  public resolveSelectionObject(
    page: number,
    selectionBBox: BoundingBox,
    selectedText: string
  ): DocumentObject | null {
    const candidates = this.tree.search({
      minX: Math.min(selectionBBox.x0, selectionBBox.x1),
      minY: Math.min(selectionBBox.y0, selectionBBox.y1),
      maxX: Math.max(selectionBBox.x0, selectionBBox.x1),
      maxY: Math.max(selectionBBox.y0, selectionBBox.y1),
    });

    const pageCandidates = candidates.filter((item) => item.page === page);
    if (pageCandidates.length === 0) return null;

    let bestMatch: DocumentObject | null = null;
    let maxOverlap = 0;

    for (const item of pageCandidates) {
      const ix0 = Math.max(selectionBBox.x0, item.minX);
      const iy0 = Math.max(selectionBBox.y0, item.minY);
      const ix1 = Math.min(selectionBBox.x1, item.maxX);
      const iy1 = Math.min(selectionBBox.y1, item.maxY);

      if (ix1 > ix0 && iy1 > iy0) {
        const overlapArea = (ix1 - ix0) * (iy1 - iy0);
        if (overlapArea > maxOverlap) {
          maxOverlap = overlapArea;
          bestMatch = item.object;
        }
      }
    }

    return bestMatch;
  }

  /**
   * Extracts surrounding text context for a target document object from surrounding lines.
   */
  public extractSurroundingContext(page: number, obj: DocumentObject): string {
    const pageItems = this.pageItems.get(page);
    if (!pageItems) return obj.text_content || "";

    const [_, y0, __, y1] = obj.bounding_box;
    const contextItems = pageItems.filter((item) => {
      if (!item.object.text_content) return false;
      return Math.abs(item.minY - y0) < 150 || Math.abs(item.maxY - y1) < 150;
    });

    return contextItems.map((item) => item.object.text_content).join("\n");
  }
}

export const spatialIndex = new SpatialDocumentIndex();
