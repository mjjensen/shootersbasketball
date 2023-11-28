PREFIX = $(HOME)/basketball/shooters

distfile = dist/sbci-0.1-py3-none-any.whl

# _PYTHON_SYSCONFIGDATA_NAME=_sysconfigdata__linux_x86_64-linux-gnu

all: $(distfile)

$(distfile): sbci/*.py
	#python3 setup.py install --prefix "$(PREFIX)" \
	#	--single-version-externally-managed --root=/
	rm -f $(distfile)
	python3.8 -m build --wheel

install: all
	python3.8 -m pip install --prefix "$(PREFIX)" $(distfile)

uninstall:
	#rm -rf "$(PREFIX)/bin" "$(PREFIX)/lib"
	python3.8 -m pip -v uninstall -y sbci

clean:
	find . -name '*.pyc' -exec rm -f '{}' ';'
	rm -rf build dist sbci.egg-info
