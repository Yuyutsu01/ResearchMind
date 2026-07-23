/**
 * Document Model Definitions for ResearchMind
 * Represents the hierarchical semantic structure of a scientific paper.
 */

export type ObjectType = 
  | "text"
  | "paragraph"
  | "equation"
  | "figure"
  | "table"
  | "caption"
  | "citation"
  | "section_header"
  | "footer";

export interface BoundingBox {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
}

export interface DocumentObject {
  id: string;
  type: ObjectType;
  page: number;
  bounding_box: [number, number, number, number]; // [x0, y0, x1, y1]
  text_content: string;
  parent_id?: string | null;
  section_title?: string | null;
  surrounding_context?: string | null;
  metadata?: Record<string, any>;
  relationships?: Array<{ target_id: string; relationship_type: string }>;
}

export interface DocumentHierarchy {
  paper_id: string;
  title?: string;
  sections: Array<{
    id: string;
    title: string;
    paragraphs: DocumentObject[];
  }>;
  figures: DocumentObject[];
  tables: DocumentObject[];
  equations: DocumentObject[];
  citations: DocumentObject[];
}

export interface SelectionPayload {
  type: "selection";
  text: string;
  selection_type: string;
  id?: string | null;
  document_object?: Partial<DocumentObject>;
}
