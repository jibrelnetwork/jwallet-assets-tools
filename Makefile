validate:
	python -m tools validate mainnet/assets.json --node="https://main-node.jwallet.network/" --progress
	python -m tools validate ropsten/assets.json --node="https://ropsten-node.jwallet.network/" --progress

validate-debug:
	python -m tools validate mainnet/assets.json --node="https://main-node.jwallet.network/" --loglevel DEBUG
	python -m tools validate ropsten/assets.json --node="https://ropsten-node.jwallet.network/" --loglevel DEBUG

validate-fast:
	python -m tools validate mainnet/assets.json --node="https://main-node.jwallet.network/" --fast --loglevel=ERROR
	python -m tools validate ropsten/assets.json --node="https://ropsten-node.jwallet.network/" --fast --loglevel=ERROR

pre-commit: validate-fast

lint: validate-fast

test:
	pytest

hooks:
	echo "#!/usr/bin/env bash\nmake pre-commit" > .git/hooks/pre-commit
	@echo "Pre-commit hook installed"

