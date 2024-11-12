import json

with open('specialties.json', 'r') as json_file:
    data = json.load(json_file)

# SQL statements for inserting department data
insert_departments = "\n".join([f"INSERT INTO department (name) VALUES ('{department}');" for department in data.keys()])

# SQL statements for inserting specialty data
insert_specialties = ""
for department, specialties in data.items():
    department_id = f"(SELECT id FROM department WHERE name = '{department}')"
    insert_specialties += "\n".join([f"INSERT INTO specialty (name, department_id) VALUES ('{specialty}', {department_id});" for specialty in specialties])

# Combine all SQL statements
sql_script = f"{insert_departments}\n\n{insert_specialties}"

with open('department_statements.txt', 'w') as f:
    f.write(sql_script)
