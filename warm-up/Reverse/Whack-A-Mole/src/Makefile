# Whack a Mole -- build from src/:  make && make verify
#
# Build order mirrors the spec: holes are generated in Python first, the C is
# proved byte-identical against that Python, then mallet is built on top.

CC       ?= gcc
PYTHON   ?= python3
CFLAGS   ?= -O2 -s -Wall -Wextra
HOSTFLAGS = -O2 -Wall -Wextra

HERE  := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
ROOT  := $(abspath $(HERE)/..)
BUILD := $(HERE)/build
STAGE := $(BUILD)/handout
DIST  := $(ROOT)/dist

TARBALL := $(DIST)/handout.tar.gz
CRYPTO  := $(HERE)/molecrypt.c $(HERE)/molecrypt.h

.PHONY: all dist holes mallet check-parity verify play solve clean

all: dist

# --- 1/2: Python generates the holes and proves the mechanic end-to-end ------
$(BUILD)/holes.stamp: gen.py molecrypt.py flag.txt
	@mkdir -p $(BUILD)
	$(PYTHON) gen.py
	@touch $@

holes: $(BUILD)/holes.stamp

# --- 3: C mirror, gated on parity with the Python ---------------------------
$(BUILD)/parity: parity.c $(CRYPTO)
	@mkdir -p $(BUILD)
	$(CC) $(HOSTFLAGS) -I$(HERE) parity.c molecrypt.c -o $@

$(BUILD)/parity.stamp: $(BUILD)/parity molecrypt.py
	$(BUILD)/parity > $(BUILD)/parity.c.txt
	$(PYTHON) molecrypt.py > $(BUILD)/parity.py.txt
	diff -u $(BUILD)/parity.py.txt $(BUILD)/parity.c.txt
	@echo "molecrypt.c and molecrypt.py agree"
	@touch $@

check-parity: $(BUILD)/parity.stamp

# --- 4: the shipped binary --------------------------------------------------
$(STAGE)/mallet: mallet.c $(CRYPTO) $(BUILD)/parity.stamp
	@mkdir -p $(STAGE)
	$(CC) $(CFLAGS) -I$(HERE) mallet.c molecrypt.c -o $@

mallet: $(STAGE)/mallet

# --- 7: package -------------------------------------------------------------
$(TARBALL): $(STAGE)/mallet $(BUILD)/holes.stamp handout-README.txt
	@mkdir -p $(DIST)
	cp handout-README.txt $(STAGE)/README.txt
	chmod 444 $(STAGE)/holes/*.bin
	tar czf $@ -C $(STAGE) mallet README.txt holes
	@echo "packaged $@"

dist: $(TARBALL)

# --- 6: every invariant in spec section 8 -----------------------------------
verify: $(TARBALL)
	$(PYTHON) verify.py

# --- author conveniences ----------------------------------------------------
play: $(BUILD)/holes.stamp
	$(PYTHON) gen.py --play

solve: $(TARBALL)
	$(PYTHON) $(ROOT)/solver/solve.py $(STAGE)

clean:
	chmod -f 644 $(STAGE)/holes/*.bin 2>/dev/null || true
	rm -rf $(BUILD) $(TARBALL)
