
python3 -m coverage run --source=telemetry -m pytest .
python3 -m coverage report --fail-under=100
