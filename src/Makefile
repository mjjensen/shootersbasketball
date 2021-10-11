PREFIX = $(HOME)/basketball/shooters

all:

# _PYTHON_SYSCONFIGDATA_NAME=_sysconfigdata__linux_x86_64-linux-gnu
install: all
	python3 setup.py install --prefix "$(PREFIX)" \
		--single-version-externally-managed --root=/

uninstall:
	rm -rf "$(PREFIX)/bin" "$(PREFIX)/lib"

clean:
	find . -name '*.pyc' -exec rm -f '{}' ';'
	rm -rf build dist sbci.egg-info
