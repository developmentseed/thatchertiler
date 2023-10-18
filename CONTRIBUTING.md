# Contributing

Issues and pull requests are more than welcome.

### dev install

```bash
python -m pip install pip -U
git clone https://github.com/developmentseed/thatchertiler.git
cd thatchertiler
python -m pip install -e ".[test,dev]"
```

You can then run the tests with the following command:

```sh
python -m pytest --cov thatchertiler --cov-report term-missing -s -vv
```

### pre-commit

This repo is set to use `pre-commit` to run *isort*, *flake8*, *pydocstring*, *black* ("uncompromising Python code formatter") and mypy when committing new code.

```bash
$ pre-commit install
```
