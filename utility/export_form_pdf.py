from form_builder.cursor_db import get_form, get_form_fields
from django.http import HttpResponse
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet


def export_form_pdf(form_name):
    """
    Creates and returns a PDF file for download containing form data
    
    Args:
        form_name: The name of the form/table to export
        
    Returns:
        HttpResponse with PDF file attachment
    """
    # Get data from database
    form_data = get_form(form_name)
    form_fields = get_form_fields(form_name)
    
    # Create HTTP response with PDF content type
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{form_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
    
    # Create the PDF document using ReportLab
    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    
    
    # Prepare data for table
    table_data = [form_fields]  # Headers row
    
    # Add data rows
    for record in form_data:
        # Convert record tuple to list for easier manipulation
        row_data = list(record)
        # Skip the first two columns (ID and Created At)
        filtered_row_data = row_data[2:]
        table_data.append(filtered_row_data)
    
    # Create the table
    table = Table(table_data)
    
    # Add style to the table
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ])
    
    table.setStyle(style)
    elements.append(table)
    
    # Build the PDF document
    doc.build(elements)
    
    return response
