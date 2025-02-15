from datetime import datetime

def change_format(date: str) -> str:
    original = datetime.strptime(str(date).replace('/', '-').strip(), '%m-%d-%Y').date()
    new_format = original.strftime('%Y-%m-%d')
    return new_format

def reverse_format(date):
    original = datetime.strptime(str(date), '%Y-%m-%d').date()
    new_format = original.strftime('%m-%d-%Y')
    return new_format

