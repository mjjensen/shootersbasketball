PREFIX = $(HOME)/basketball/shooters
PYTHON = python3.13

distfile = dist/sbci-0.1-py3-none-any.whl

# _PYTHON_SYSCONFIGDATA_NAME=_sysconfigdata__linux_x86_64-linux-gnu

all: $(distfile)

$(distfile): sbci/*.py
	#python3 setup.py install --prefix "$(PREFIX)" \
	#	--single-version-externally-managed --root=/
	rm -f $(distfile)
	$(PYTHON) -m build --wheel

install: all
	-$(PYTHON) -m pip uninstall --yes sbci
	$(PYTHON) -m pip install --force-reinstall --prefix "$(PREFIX)" $(distfile)

uninstall:
	#rm -rf "$(PREFIX)/bin" "$(PREFIX)/lib"
	$(PYTHON) -m pip -v uninstall -y sbci

clean:
	find . -name '*.pyc' -exec rm -f '{}' ';'
	rm -rf build dist sbci.egg-info
