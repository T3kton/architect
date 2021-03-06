all:

#make sure python3-pytest python3-pytest-cov python3-pytest-django python3-pytest-mock are installed

test:
	py.test-3 -x --cov=architect --cov-report html --cov-report term --ds=architect.settings -vv architect

make_test_db:
	if [ -e db.sqlite3 ] ; then echo "DB Allready exists"; exit 1 ; fi
	cd local/api_server && ./manage.py migrate && ./load_test_data

start_api_server:
	cd local/api_server && ./api_server.py
