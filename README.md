## Python Version
This project was created with Python 3.11.  
Other versions of python may not work as intended.

## Setting up your environment
The recommended way to install dependencies is with a virtual environment. You can create one with the command
```shell
python3 -m venv ./venv
```
Next, source your environment
```shell
# Linux, MacOS
source venv/bin/activate
# Windows PowerShell
PS C:\> venv/bin/Activate.ps1
```
### Install the requirements
```shell
(venv) > pip install -r requirements.txt
```
Everything must be installed properly to run.

### Configuring your .env file
Open the file `.env` in the root of the project. If one does not exist, you can copy `.env.sample -> .env`.  
Open the file in your editor of choice and fill out the connection string details. You must provide the exact information
* Host
* Username
* Password
* Schema Name

For the connection to initialize properly

## Running the UI

To run the process controller application, the UI file must be used to generate a python module using the following
command:

```shell
python -m PyQt6.uic.pyuic -x databaseui/ui/views/app.ui -o databaseui/ui/app.py
```

Once the UI file is built, you can run the application with
```shell
python databaseui/main.py
```
