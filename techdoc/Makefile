GRAPHS = acceptorsm.png proposersm.png

all: $(GRAPHS)

%.png:%.dot
	dot -Tpng -o$@ $<

clean:
	rm -f $(GRAPHS)
