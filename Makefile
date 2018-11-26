lint:
	pylama
	flake8 --max-line-length=100

test:
	pytest --cov=jwallet_tools
