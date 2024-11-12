import json

from sqlalchemy import text


def generate_sql_statements(data):
    statements = []

    for entry in data:
        # Insert data into 'person' table
        person_insert = text(
            f"INSERT INTO person (first_name, last_name) VALUES ('{entry['first_name']}', '{entry['last_name']}');")
        statements.append(person_insert)

        if not entry['is_patient']:
            continue

        # Get the ID of the inserted person
        get_person_id = text("SET @person_id = LAST_INSERT_ID();")
        statements.append(get_person_id)

        # Insert data into 'patient' table using the obtained person ID
        patient_insert = text((
            f"INSERT INTO patient (person_id, gender, sex, sexual_orientation, DOB, phone_number, email, address) "
            f"VALUES (@person_id, '{entry['gender']}', '{entry['sex']}', '{entry.get('sexual_orientation', '')}', "
            f"'{entry['DOB']}', '{entry.get('phone_number', '')}', '{entry.get('email', '')}', '{entry.get('address', '')}');"
        ))
        statements.append(patient_insert)

    return statements


def main():
    # Read JSON file
    with open('patient.json', 'r') as json_file:
        data = json.load(json_file)

    for entry in data:
        for key, value in entry.items():
            if not isinstance(value, str):
                continue
            entry[key] = value.replace("'", "''")

    # Generate SQL statements
    sql_statements = generate_sql_statements(data)

    # Write SQL statements to file
    with open('patient_statements.txt', 'w') as output_file:
        for statement in sql_statements:
            output_file.write(statement.text + '\n')


if __name__ == "__main__":
    main()
