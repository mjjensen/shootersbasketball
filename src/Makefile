PREFIX = $(HOME)/basketball/shooters

all:

# _PYTHON_SYSCONFIGDATA_NAME=_sysconfigdata__linux_x86_64-linux-gnu
install:
	#python3 setup.py install --prefix "$(PREFIX)" \
	#	--single-version-externally-managed --root=/
	rm -f dist/sbci-0.1-py3-none-any.whl
	python3 -m build --wheel
	python3 -m pip install --force-reinstall --prefix "$(PREFIX)" \
		dist/sbci-0.1-py3-none-any.whl

uninstall:
	rm -rf "$(PREFIX)/bin" "$(PREFIX)/lib"

clean:
	find . -name '*.pyc' -exec rm -f '{}' ';'
	rm -rf build dist sbci.egg-info
