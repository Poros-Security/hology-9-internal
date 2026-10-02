CXX ?= g++
STRIP ?= strip

CXXFLAGS := -std=c++17 -O2 -fPIE -fstack-protector-strong -D_FORTIFY_SOURCE=2
LDFLAGS := -pie -Wl,-z,relro,-z,now -Wl,-z,noexecstack \
	-Wl,--export-dynamic-symbol=dog_default_trick \
	-Wl,--export-dynamic-symbol=rabbit_default_hint \
	-Wl,--export-dynamic-symbol=print_flag

.PHONY: all clean

all: suipp

suipp: chall.cpp
	$(CXX) chall.cpp -o $@ $(CXXFLAGS) $(LDFLAGS)
	$(STRIP) --strip-all $@

clean:
	rm -f suipp *.o core core.*
