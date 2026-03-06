import re

def chunk_text(text, max_length=800):
    sections = re.split(r'\n(?=\d+(\.\d+)*\s+)', text)

    chunks = []

    for section in sections:
        section = section.strip()
        if not section:
            continue

        if len(section) <= max_length:
            chunks.append(section)
        else:
            paragraphs = section.split("\n\n")
            current = ""

            for p in paragraphs:
                if len(current) + len(p) < max_length:
                    current += p + "\n\n"
                else:
                    chunks.append(current.strip())
                    current = p + "\n\n"

            if current:
                chunks.append(current.strip())

    return chunks