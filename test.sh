
python3 -m coverage run --omit="**/tests/*,**/migrations/*,manage.py" manage.py test
python3 -m coverage report --fail-under=100
python3 -m coverage html
