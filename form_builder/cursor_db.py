from django.db import connection
import json



def list_forms():
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, name FROM form_builder_customform")
        return cursor.fetchall()



def get_form_fields(form_name):
    with connection.cursor() as cursor:
        # Get the table name from the form_builder_customform table
        cursor.execute("SELECT id FROM form_builder_customform WHERE name = %s", [form_name])
        form_id = cursor.fetchone()[0]
        table_name = f"form_{form_id}"

        # Get the column names using PRAGMA table_info
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        # Filter out id and created_at columns and return column names
        return [col[1] for col in columns if col[1] not in ('id', 'created_at')]


def add_form(form_name, fields):
    with connection.cursor() as cursor:

        # Insert the form metadata
        cursor.execute(
            "INSERT INTO form_builder_customform (name) VALUES (%s) RETURNING id",
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



def get_form(form_name):
    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT * FROM {form_name}"
        )

        return cursor.fetchall()




def add_record(form_name, records: list):
    with connection.cursor() as cursor:
        cursor.execute(
            f"INSERT INTO {form_name} (record) VALUES (%s)",
            records
        )


def remove_record(form_name, record_id):
    with connection.cursor() as cursor:
        cursor.execute(
            f"DELETE FROM {form_name} WHERE id = %s",
            [record_id]
        )


def update_record(form_name, record_id, record):
    with connection.cursor() as cursor:
        cursor.execute(
            f"UPDATE {form_name} SET record = %s WHERE id = %s",
            [record, record_id]
        )

