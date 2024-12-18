import re
from langchain.text_splitter import RecursiveCharacterTextSplitter


class TextProcessor:
    def __init__(self, text: str):
        self.text = text

    def chunks_by_paragraph(self):
        return self.text.split('\n\n')

    def chunks_with_fixed_length(self, length: int):
        return [self.text[i:i+length] for i in range(0, len(self.text), length)]

    def chunks_with_overlap(self, chunk_size: int, overlap: int):
        words = self.text.split()
        segments = []

        current_segment = []
        current_length = 0

        for word in words:
            if current_length + len(word) + 1 > chunk_size:
                segments.append(" ".join(current_segment))
                current_segment = current_segment[-overlap:]
                current_length = sum(len(w) for w in current_segment) + len(current_segment) - 1
            current_segment.append(word)
            current_length += len(word) + 1

        if current_segment:
            segments.append(" ".join(current_segment))
        return segments

    def chunks_with_recursion(self, chunk_size: int, chunk_overlap: int):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len)
        segments = text_splitter.split_text(self.text)

        return segments



