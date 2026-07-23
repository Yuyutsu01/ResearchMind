/**
 * SemanticResolver for ResearchMind (Phase 8)
 * 
 * Maps raw browser text selections and bounding rectangles to structured semantic document objects
 * containing section headings, parent paragraphs, surrounding context, and references.
 */

import { DocumentObject, BoundingBox } from "./document_model";
import { spatialIndex } from "./spatial_index";

export interface SemanticContextPayload {
  page: number;
  section: string | null;
  paragraph: string | null;
  text: string;
  bbox: BoundingBox;
  context: string;
  object_id?: string | null;
  object_type?: string | null;
}

export class SemanticResolver {
  /**
   * Resolves a selection into a full semantic document context payload for the Swarm Orchestrator.
   */
  public resolveContext(
    page: number,
    selectionBBox: BoundingBox,
    selectedText: string,
    matchedObj?: DocumentObject | null
  ): SemanticContextPayload {
    // If no matched object passed, query RBush spatial index
    const resolvedObj = matchedObj || spatialIndex.resolveSelectionObject(page, selectionBBox, selectedText);

    const surroundingContext = resolvedObj
      ? spatialIndex.extractSurroundingContext(page, resolvedObj)
      : selectedText;

    return {
      page,
      section: resolvedObj?.section_title || null,
      paragraph: resolvedObj?.text_content || selectedText,
      text: selectedText,
      bbox: selectionBBox,
      context: surroundingContext,
      object_id: resolvedObj?.id || null,
      object_type: resolvedObj?.type || "text",
    };
  }
}

export const semanticResolver = new SemanticResolver();
