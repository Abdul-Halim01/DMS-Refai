from form_builder.cursor_db import get_form, get_form_fields
from openpyxl import Workbook
from django.http import HttpResponse
from datetime import datetime


def export_form_excel(form_name):
    """
    Creates and returns an Excel file for download containing form data
    
    Args:
        form_name: The name of the form/table to export
        
    Returns:
        HttpResponse with Excel file attachment
    """
    # Get data from database
    form_data = get_form(form_name)
    form_fields = get_form_fields(form_name)
    
    # Create a new workbook and select the active worksheet
    wb = Workbook()
    ws = wb.active
    ws.title = form_name
    
    # Add headers (only form fields, excluding ID and Created At)
    headers = form_fields
    ws.append(headers)
    
    # Add data rows
    for record in form_data:
        # Convert record tuple to list for easier manipulation
        row_data = list(record)
        # Skip the first two columns (ID and Created At)
        filtered_row_data = row_data[2:]
        ws.append(filtered_row_data)
    
    # Prepare response with Excel file
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{form_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
    
    # Save the workbook to the response
    wb.save(response)
    
    return response
