DEFAULT_CHUNK_SIZE = 4_000
DEFAULT_CHUNK_OVERLAP = 400


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """Split text into overlapping chunks without discarding content."""

    if chunk_size <= 0:
        raise ValueError("Chunk size must be greater than zero.")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "Overlap must be zero or greater and smaller than chunk size."
        )

    cleaned_text = text.strip()

    if not cleaned_text:
        return []

    chunks = []
    start = 0

    while start < len(cleaned_text):
        proposed_end = min(
            start + chunk_size,
            len(cleaned_text),
        )
        end = proposed_end

        # Prefer splitting at a line break instead of mid-line.
        if proposed_end < len(cleaned_text):
            line_break = cleaned_text.rfind(
                "\n",
                start,
                proposed_end,
            )

            if line_break > start + (chunk_size // 2):
                end = line_break

        chunk = cleaned_text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(cleaned_text):
            break

        # Repeat a small part so context isn't lost between chunks.
        start = max(
            end - overlap,
            start + 1,
        )

    return chunks