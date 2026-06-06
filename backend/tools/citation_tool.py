import re

def format_citation(title: str, authors: list[str], year: str, url: str = None, style: str = "APA") -> str:
    """
    Format a citation dynamically in different bibliography styles.
    """
    if not authors:
        authors = ["Unknown Author"]
        
    # Format author list for bibliography
    if len(authors) == 1:
        auth_str = authors[0]
    elif len(authors) == 2:
        auth_str = f"{authors[0]} & {authors[1]}"
    else:
        auth_str = f"{authors[0]} et al."
        
    year_str = year or "n.d."
    
    if style == "APA":
        cit = f"{auth_str} ({year_str}). {title}."
        if url:
            cit += f" Retrieved from {url}"
        return cit
        
    elif style == "MLA":
        cit = f"{auth_str}. \"{title}.\" {year_str}."
        if url:
            cit += f" Web. <{url}>."
        return cit
        
    elif style == "Chicago":
        cit = f"{auth_str}. {year_str}. \"{title}.\""
        if url:
            cit += f" {url}."
        return cit
        
    elif style == "BibTeX":
        # Generate bib key
        clean_author = re.sub(r'[^a-zA-Z]', '', authors[0].split()[-1]).lower() if authors[0].split() else "author"
        clean_title = re.sub(r'[^a-zA-Z]', '', title.split()[0]).lower() if title.split() else "title"
        bib_key = f"{clean_author}{year_str}{clean_title}"
        
        authors_joined = " and ".join(authors)
        bib = f"@article{{{bib_key},\n"
        bib += f"  author = {{{authors_joined}}},\n"
        bib += f"  title = {{{title}}},\n"
        bib += f"  year = {{{year_str}}}"
        if url:
            bib += f",\n  url = {{{url}}}"
        bib += "\n}"
        return bib
        
    return f"{auth_str}, {title}, {year_str}"

def validate_citations(text: str, references: list[str]) -> dict:
    """
    Checks if in-text citations (like '[1]', '[Vaswani et al., 2017]')
    have a matching entry in the reference list.
    """
    matches = re.findall(r'\[([\d,\s\-]+)\]', text)
    citation_numbers = set()
    for m in matches:
        for num in re.split(r'[,\s\-]+', m):
            if num.strip().isdigit():
                citation_numbers.add(int(num.strip()))
                
    # Also find bracketed author names e.g., (Vaswani et al., 2017)
    author_matches = re.findall(r'\(([A-Za-z\s]+et\s+al\.\,?\s+\d{4})\)', text)
    
    invalid = []
    total = len(citation_numbers) + len(author_matches)
    
    # Simple validation check: if [N] is used, check if we have at least N references
    for num in citation_numbers:
        if num > len(references) or num <= 0:
            invalid.append(f"In-text citation [{num}] has no matching bibliography entry.")
            
    # For author-date, check if author's last name appears in any reference
    for cit in author_matches:
        author_name = cit.split()[0].lower()
        found = False
        for ref in references:
            if author_name in ref.lower():
                found = True
                break
        if not found:
            invalid.append(f"Author citation ({cit}) has no matching bibliography entry.")
            
    score = 1.0
    if total > 0:
        score = max(0.0, 1.0 - (len(invalid) / total))
        
    return {
        "score": score,
        "valid": len(invalid) == 0,
        "total_citations_found": total,
        "invalid_citations": invalid
    }
