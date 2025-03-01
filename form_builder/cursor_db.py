from django.db import connection
import json

def create_form(form_name, fields):
    with connection.cursor() as cursor:
        # Create the forms metadata table if it doesn't exist
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS form_builder (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        
        # Insert the form metadata
        cursor.execute(
            "INSERT INTO form_builder (name) VALUES (%s) RETURNING id",
            [form_name]
        )
        form_id = cursor.fetchone()[0]
        
        # Create the dynamic form table
        table_name = f"form_{form_id}"
        create_table_sql = f"""
            CREATE TABLE {table_name} (
                id SERIAL PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        """
        
        # Add fields dynamically based on the fields parameter
        field_definitions = []
        for field in fields:
            field_name = field['name'].lower().replace(' ', '_')
            field_type = field['type'].upper()
            
            if field_type == 'VARCHAR':
                max_length = field.get('max_length', 255)
                field_def = f"{field_name} VARCHAR({max_length})"
            elif field_type == 'INTEGER':
                field_def = f"{field_name} INTEGER"
            elif field_type == 'TEXT':
                field_def = f"{field_name} TEXT"
            elif field_type == 'DATE':
                field_def = f"{field_name} DATE"
            elif field_type == 'BOOLEAN':
                field_def = f"{field_name} BOOLEAN"
            elif field_type == 'DECIMAL':
                field_def = f"{field_name} DECIMAL(10,2)"
            else:
                continue  # Skip unknown field types
                
            if field.get('required', False):
                field_def += " NOT NULL"
                
            field_definitions.append(field_def)
        
        # Add all field definitions to the CREATE TABLE statement
        create_table_sql += ",\n".join(field_definitions)
        create_table_sql += "\n)"
        
        # Create the actual table
        cursor.execute(create_table_sql)
        
        return {
            'success': True,
            'form_id': form_id,
            'table_name': table_name
        }
