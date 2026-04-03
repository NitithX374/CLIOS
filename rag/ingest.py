import os
import re
import pickle
import fitz  # PyMuPDF
import faiss
import numpy as np
from embedder import embed

RFC_DIR = "../data/rfc"
OUTPUT_DIR = "../data/rag_indices"

PROTOCOL_MAP = {
    "1349": "TCP", # IP/TCP
    "2328": "OSPF",
    "2453": "RIP",
    "768": "UDP",
    "7868": "EIGRP",
    "791": "IP",
    "9293": "TCP",
    "792": "ICMP",
    "826": "ARP",
    "1812": "ROUTER"
}

def clean_text(text):
    # Basic cleanup for whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def is_header_footer(line):
    # Very heuristic check for RFC header/footers
    line_lower = line.lower()
    if re.search(r'\[page \d+\]', line_lower): return True
    if re.search(r'^rfc \d+', line_lower): return True
    return False

def parse_rfc_pdf(filepath):
    doc = fitz.open(filepath)
    text_content = []
    
    for page in doc:
        blocks = page.get_text("blocks")
        for b in blocks:
            text = b[4].strip()
            if not text: continue
            
            # Remove line by line if it's header/footer
            lines = text.split('\n')
            valid_lines = [l for l in lines if not is_header_footer(l)]
            if valid_lines:
                text_content.append(" ".join(valid_lines))
                
    full_text = " ".join(text_content)
    full_text = clean_text(full_text)
    
    # Split into sections based on e.g., "3.2. State Machine"
    # Matches "1. ", "3.2 ", "A.1 ", etc.
    section_pattern = r'(\n\d+(?:\.\d+)*\s+[A-Z][^\n]+)'
    
    # A simplified split since PDFs might lose exact newlines. 
    # Let's use a heuristic: digits followed by dots, space, and capital letter.
    sections_raw = re.split(r'(\b\d+(?:\.\d+)*\s+[A-Z][A-Za-z\s]+)(?=\b\d+(?:\.\d+)*\s+[A-Z])', full_text)
    
    if len(sections_raw) == 1:
        # Fallback if parsing fails
        return [{"section": "1.0", "title": "General", "text": full_text}]
        
    sections = []
    current_title = "General"
    current_text = sections_raw[0]
    if current_text.strip():
        sections.append({"section": "0.0", "title": current_title, "text": current_text})
        
    for i in range(1, len(sections_raw), 2):
        title_part = sections_raw[i].strip()
        body_part = sections_raw[i+1] if i+1 < len(sections_raw) else ""
        
        # extract section number
        match = re.match(r'^(\d+(?:\.\d+)*)\s+(.*)', title_part)
        if match:
            sec_num = match.group(1)
            title = match.group(2)
        else:
            sec_num = "X"
            title = title_part
            
        sections.append({
            "section": sec_num,
            "title": title,
            "text": clean_text(body_part)
        })
        
    return sections

def get_chunks(text, chunk_size=800, overlap=200):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks

def build_indexes():
    # protocol -> { "sections": index, "chunks": index, "metadata": [] }
    protocol_data = {}
    
    for filename in os.listdir(RFC_DIR):
        if not filename.endswith(".pdf"):
            continue
            
        rfc_match = re.search(r'rfc(\d+)', filename)
        if not rfc_match: continue
        rfc_num = rfc_match.group(1)
        protocol = PROTOCOL_MAP.get(rfc_num, "UNKNOWN").upper()
        
        print(f"Processing {filename} -> RFC {rfc_num} ({protocol})")
        
        sections = parse_rfc_pdf(os.path.join(RFC_DIR, filename))
        
        if protocol not in protocol_data:
            protocol_data[protocol] = {"sections": [], "chunks": []}
            
        for sec in sections:
            sec_text = sec["text"]
            if not sec_text: continue
            
            # Embed section (using first 1000 chars as representative)
            sec_embed_text = f"Section {sec['section']} - {sec['title']}\n{sec_text[:1000]}"
            sec["embedding"] = embed(sec_embed_text)
            sec["rfc_version"] = rfc_num
            sec["protocol"] = protocol
            
            sub_chunks = get_chunks(sec_text)
            chunk_recs = []
            for chunk_text in sub_chunks:
                chunk_recs.append({
                    "text": chunk_text,
                    "embedding": embed(chunk_text),
                    "section": sec["section"],
                    "title": sec["title"],
                    "rfc_version": rfc_num,
                    "protocol": protocol
                })
                
            sec["chunk_records"] = chunk_recs
            protocol_data[protocol]["sections"].append(sec)

    for proto, data in protocol_data.items():
        if proto == "UNKNOWN": continue
        
        secs = data["sections"]
        if not secs: continue
        
        # Build Section FAISS
        dim = len(secs[0]["embedding"])
        sec_index = faiss.IndexFlatL2(dim)
        sec_embeddings = np.array([s["embedding"] for s in secs], dtype="float32")
        sec_index.add(sec_embeddings)
        
        # Build Chunk FAISS
        all_chunks = []
        for s in secs: all_chunks.extend(s["chunk_records"])
        chunk_index = faiss.IndexFlatL2(dim)
        chunk_embeddings = np.array([c["embedding"] for c in all_chunks], dtype="float32")
        chunk_index.add(chunk_embeddings)
        
        # Save indexes
        faiss.write_index(sec_index, os.path.join(OUTPUT_DIR, f"faiss_{proto}_sections.index"))
        faiss.write_index(chunk_index, os.path.join(OUTPUT_DIR, f"faiss_{proto}_chunks.index"))
        
        # Exclude raw embeddings from section metadata to save space, but keep for chunks
        for s in secs: s.pop("embedding", None)

        
        metadata = {
            "sections": secs,
            "chunks": all_chunks
        }
        
        with open(os.path.join(OUTPUT_DIR, f"metadata_{proto}.pkl"), "wb") as f:
            pickle.dump(metadata, f)

if __name__ == "__main__":
    build_indexes()
