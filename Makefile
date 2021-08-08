# -----------------------------------------------------------------------------
# Web/App server (Python/Django)

env:
	pipenv install

env-dev:
	pipenv install --dev

tests:
	pipenv run tests

clean:
	rm -rf ./.pytest_cache/
	find . | grep -E "(__pycache__|\.pyc|\.pyo)" | xargs rm -rf

reset: clean
	pipenv --rm
	rm Pipfile.lock
