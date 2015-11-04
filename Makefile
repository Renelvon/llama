PYTHON=python3
PREPARE_FLAGS=--prepare -pd
OPT=-OO
SOURCEFILES=main.py ./compiler/*.py
TABLEPATH=./tables
BINPATH=./bin
TESTPATH=./tests

.PHONY: check clean flake8check functionaltest prepare pylintcheck test unittest

all: clean check prepare test

pylintcheck:
	pylint --rcfile .pylintrc $(SOURCEFILES) $(TESTPATH)

flake8check:
	flake8 --ignore=E221,N802 ./compiler/lex.py
	flake8 --ignore=E501 ./compiler/parse.py
	flake8 --ignore=F821 ./compiler/infer.py
	flake8 --ignore=N802,N803,N806 --exclude=lex.py,parse.py,infer.py $(SOURCEFILES)
	flake8 --ignore=E731,N802 --exclude=__init__.py $(TESTPATH)/*.py

check: flake8check pylintcheck

test: unittest functionaltest

unittest:
	nosetests --with-coverage --cover-package=compiler --cover-inclusive

functionaltest: $(BINPATH)/ftest.sh
	$(BINPATH)/ftest.sh

prepare:
	$(PYTHON) main.py $(PREPARE_FLAGS)
	$(BINPATH)/ctest.sh

clean:
	$(RM) $(TABLEPATH)/*.py $(TABLEPATH)/parser.out .coverage
