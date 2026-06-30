import pymupdf4llm
import pathlib

pdf_file_path = "Cleveland-Clinic-Challenge-Statement-vF-1.pdf" 
md_file_name = f"{pathlib.Path(pdf_file_path).stem}.md"
md_text = pymupdf4llm.to_markdown(pdf_file_path)
pathlib.Path(md_file_name).write_bytes(md_text.encode())
