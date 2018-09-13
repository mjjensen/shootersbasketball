DESTDIR = /tmp
RECORD = $(DESTDIR)/.sbci-record

all:

install: all
	python setup.py install \
		--install-layout deb \
		--record "$(RECORD)" \
		--root "$(DESTDIR)"

clean:
	rm -f "$(RECORD)"
	find . -name '*.pyc' -exec rm -f '{}' ';'
	rm -rf build sbci.egg-info
