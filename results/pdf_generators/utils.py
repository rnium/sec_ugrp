import fitz
import io
from django.conf import settings

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


def get_fonts_css_txt(font_names):
    css_text = ""
    for font_name in font_names.keys():
        font_path = settings.BASE_DIR/f"results/pdf_generators/fonts/{font_names[font_name]}"
        css_text += f"""@font-face {{
                        font-family: {font_name};
                        src: url(file://{font_path});}}"""
    return css_text


BANGLA_ORDINAL_MAPPING = {
    1 : '১ম',
    2 : '২য়',
    3 : '৩য়',
    4 : '৪র্থ',
    5 : '৫ম',
    6 : '৬ষ্ঠ',
    7 : '৭ম',
    8 : '৮ম'
}

BANGLA_NUMBER_MAPPING = {
    0 : '০',
    1 : '১',
    2 : '২',
    3 : '৩',
    4 : '৪',
    5 : '৫',
    6 : '৬',
    7 : '৭',
    8 : '৮',
    9 : '৯'
}

def get_bangla_ordinal_upto_eight(n):
    return BANGLA_ORDINAL_MAPPING.get(n, '*')

def get_bangla_number(n):
    bn_num = ''
    for c in str(n):
        if bn_char:=BANGLA_NUMBER_MAPPING.get(int(c.strip()), False):
            print(bn_char, flush=1)
            bn_num += bn_char
    return bn_num

def get_year_number_in_bangla(year):
    return get_bangla_number(year)