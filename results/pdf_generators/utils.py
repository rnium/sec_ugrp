import fitz
import io

def merge_pdfs_from_buffers(pdf_buffers):
    # Create a new PDF document to store the merged pages
    merged_pdf = fitz.open()

    # Iterate through each PDF buffer and add pages to the merged document
    for buffer in pdf_buffers:
        pdf_document = fitz.open("pdf", buffer)
        merged_pdf.insert_pdf(pdf_document)

    # Save the merged PDF to a buffer
    merged_buffer = io.BytesIO()
    merged_pdf.save(merged_buffer)
    merged_buffer.seek(0)  # Set the buffer's cursor to the beginning
    merged_pdf.close()

    return merged_buffer