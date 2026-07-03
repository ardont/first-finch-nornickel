import os
import fitz  # PyMuPDF
from docx import Document
from pptx import Presentation
import pandas as pd

class DocumentParser:
    def parse_pdf(self, file_path: str) -> str:
        text = ""
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text() + "\n"
        return text

    def parse_docx(self, file_path: str) -> str:
        doc = Document(file_path)
        text = []
        for paragraph in doc.paragraphs:
            text.append(paragraph.text)
        return "\n".join(text)

    def parse_pptx(self, file_path: str) -> str:
        prs = Presentation(file_path)
        text = []
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text.append(shape.text)
        return "\n".join(text)

    def parse_xlsx(self, file_path: str) -> list[dict]:
        """
        Парсинг xlsx с возвратом списка листов в виде словарей
        """
        xls = pd.ExcelFile(file_path)
        sheets_data = []
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name)
            sheets_data.append({
                "sheet_name": sheet_name,
                "data": df.to_dict(orient="records"),
                "text_summary": df.to_string()
            })
        return sheets_data

    def chunk_text(self, text: str, chunk_size: int = 600, overlap: int = 100) -> list[str]:
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk:
                chunks.append(chunk)
        return chunks

parser = DocumentParser()
