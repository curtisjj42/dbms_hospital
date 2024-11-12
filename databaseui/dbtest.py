from dataclasses import asdict
from pprint import pprint
import mysql.connector
# import MySQLdb
from databaseui.database.db_types import Treatment, DBCredentials
from databaseui.env import load_config


def main() -> None:
    config = load_config()
    db_params: DBCredentials = DBCredentials(
        user=config.User,
        passwd=config.Password,
        host=config.Host,
        db_name=config.Database
    )
    with mysql.connector.connect(**asdict(db_params)) as db:
        print('Connected to MariaDB')
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM `treatment`")
            result = list(map(lambda elem: Treatment(*elem), cursor.fetchall()))
            pprint(result)


if __name__ == '__main__':
    main()
