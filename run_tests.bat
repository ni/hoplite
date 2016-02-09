virtualenv venv
venv\Scripts\pip install -r .\tests\dependencies
venv\Scripts\easy_install.exe nose==1.3.1
venv\Scripts\python.exe setup.py install
venv\Scripts\python.exe venv\Scripts\nosetests-script.py .\tests --logging-clear-handlers --with-xunit
rmdir /s /q venv
pause