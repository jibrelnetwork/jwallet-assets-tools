lint:
	pylama
	flake8 --max-line-length=100
	mypy jwallet_tools --ignore-missing-imports

test:
	pytest --cov=jwallet_tools
