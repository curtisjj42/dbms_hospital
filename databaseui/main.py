import sys
from dotenv import load_dotenv

from databaseui.ui import create_app, run_app


def main() -> int:
    load_dotenv()
    app = create_app()
    # TODO: Init database management thread, setup tables, etc
    return run_app(app)


if __name__ == '__main__':
    ret = main()
    sys.exit(ret)
