CC ?= gcc
STRIP ?= strip
XOLLVM_VERSION := v0.10.0
XOLLVM_DIR ?= .tools/xollvm-$(XOLLVM_VERSION)
XOLLVM_CLANG ?= $(XOLLVM_DIR)/bin/clang
APPIMAGETOOL ?= .tools/appimagetool-x86_64.AppImage

RAYLIB_DIR := third_party/raylib/src
RAYLIB_A := $(RAYLIB_DIR)/libraylib.a
CPPFLAGS := -Isrc -Ithird_party/chesslib/include -I$(RAYLIB_DIR) -Ibuild/generated
BASE_CFLAGS := -std=gnu11 -Wall -Wextra -Wpedantic -Werror
DEBUG_CFLAGS := $(BASE_CFLAGS) -O1 -g3 -fPIE
RELEASE_CFLAGS := $(BASE_CFLAGS) -O2 -fPIE -DNDEBUG
OBF_CFLAGS := $(BASE_CFLAGS) -Wno-strict-prototypes -O2 -fPIE -DNDEBUG -DBLUEROSE_XOLLVM
OBF_DRIVER_FLAGS := -mllvm -enable-obfuscation \
	-mllvm -obf-seed=4777280457461355333 -mllvm -obf-deterministic
THIRD_CFLAGS := -std=gnu11 -O2 -Wno-type-limits -Wno-sign-compare
STATIC_GUI_LIBS := -Wl,-Bstatic -Wl,--start-group $(RAYLIB_A) \
	-lXrandr -lXi -lXinerama -lXcursor -lX11 -lXrender -lXfixes -lXext \
	-lxcb -lXau -lXdmcp -Wl,--end-group -Wl,-Bdynamic -lm -lpthread -ldl -lrt
FULL_STATIC_LIBS := -Wl,--start-group $(RAYLIB_A) \
	-lXrandr -lXi -lXinerama -lXcursor -lX11 -lXrender -lXfixes -lXext \
	-lxcb -lXau -lXdmcp -Wl,--end-group -lm -lpthread -ldl -lrt

APP_SRC := $(wildcard src/*.c)
CORE_SRC := $(filter-out src/main.c src/gui.c,$(APP_SRC))
THIRD_SRC := $(wildcard third_party/chesslib/src/*.c)
DEBUG_OBJ := $(APP_SRC:%.c=build/debug/%.o) $(THIRD_SRC:%.c=build/debug/%.o)
RELEASE_APP_OBJ := $(APP_SRC:%.c=build/release/%.o)
RELEASE_THIRD_OBJ := $(THIRD_SRC:%.c=build/release/%.o)
RELEASE_OBJ := $(RELEASE_APP_OBJ) $(RELEASE_THIRD_OBJ)
OBF_APP_OBJ := $(APP_SRC:%.c=build/obfuscated/%.o)
OBF_OBJ := $(OBF_APP_OBJ) $(RELEASE_THIRD_OBJ)
OBF_CORE_OBJ := $(CORE_SRC:%.c=build/obfuscated/%.o) $(RELEASE_THIRD_OBJ)
TEST_OBJ := $(CORE_SRC:%.c=build/test/%.o) $(THIRD_SRC:%.c=build/test/%.o)

.PHONY: all release unstripped static static-unstripped xollvm-setup appimagetool-setup \
	obfuscated obfuscated-unstripped obfuscated-static appimage solver test-obfuscated clean test

all: bluerose

bluerose: $(RAYLIB_A) $(DEBUG_OBJ)
	$(CC) -fPIE -pie $(DEBUG_OBJ) -o $@ $(STATIC_GUI_LIBS)

release: $(RAYLIB_A) $(RELEASE_OBJ)
	$(CC) -fPIE -pie $(RELEASE_OBJ) -o bluerose $(STATIC_GUI_LIBS)
	$(STRIP) --strip-all bluerose

unstripped: $(RAYLIB_A) $(RELEASE_OBJ)
	$(CC) -fPIE -pie $(RELEASE_OBJ) -o bluerose-unstripped $(STATIC_GUI_LIBS)

# Fully static ELF. Desktop OpenGL drivers are normally dlopen()ed by GLFW and
# remain a host-runtime limitation even though this ELF has no DT_NEEDED entries.
static: $(RAYLIB_A) $(RELEASE_OBJ)
	$(CC) -static -no-pie $(RELEASE_OBJ) -o bluerose-static $(FULL_STATIC_LIBS)
	$(STRIP) --strip-all bluerose-static

static-unstripped: $(RAYLIB_A) $(RELEASE_OBJ)
	$(CC) -static -no-pie $(RELEASE_OBJ) -o bluerose-static-unstripped $(FULL_STATIC_LIBS)

xollvm-setup: $(XOLLVM_CLANG)

$(XOLLVM_CLANG): tools/setup_xollvm.sh
	tools/setup_xollvm.sh $(XOLLVM_DIR)

obfuscated: $(RAYLIB_A) $(XOLLVM_CLANG) $(OBF_OBJ)
	$(CC) -fPIE -pie $(OBF_OBJ) -o bluerose-obfuscated $(STATIC_GUI_LIBS)
	$(STRIP) --strip-all bluerose-obfuscated

obfuscated-unstripped: $(RAYLIB_A) $(XOLLVM_CLANG) $(OBF_OBJ)
	$(CC) -fPIE -pie $(OBF_OBJ) -o bluerose-obfuscated-unstripped $(STATIC_GUI_LIBS)

obfuscated-static: $(RAYLIB_A) $(XOLLVM_CLANG) $(OBF_OBJ)
	$(CC) -static -no-pie $(OBF_OBJ) -o bluerose-obfuscated-static $(FULL_STATIC_LIBS)
	$(STRIP) --strip-all bluerose-obfuscated-static

appimagetool-setup: $(APPIMAGETOOL)

$(APPIMAGETOOL): tools/setup_appimagetool.sh
	tools/setup_appimagetool.sh $@

appimage: obfuscated $(APPIMAGETOOL) flag.enc tools/build_appimage.sh \
		tools/appimage_launcher.c tools/bluerose.desktop assets/cburnett_chess_pieces.png
	CC=$(CC) tools/build_appimage.sh bluerose-obfuscated flag.enc \
		$(APPIMAGETOOL) Bluerose-x86_64.AppImage

$(RAYLIB_A): $(RAYLIB_DIR)/raylib.h $(RAYLIB_DIR)/rcore.c $(RAYLIB_DIR)/rshapes.c \
	$(RAYLIB_DIR)/rtextures.c $(RAYLIB_DIR)/rtext.c $(RAYLIB_DIR)/rglfw.c
	$(MAKE) -C $(RAYLIB_DIR) CC=$(CC) PLATFORM=PLATFORM_DESKTOP RAYLIB_LIBTYPE=STATIC

build/debug/src/%.o: src/%.c
	@mkdir -p $(dir $@)
	$(CC) $(CPPFLAGS) $(DEBUG_CFLAGS) -c $< -o $@

build/generated/pieces_png.h: assets/cburnett_chess_pieces.png
	@mkdir -p $(dir $@)
	xxd -i -n rose_piece_png $< > $@

build/debug/src/gui.o build/release/src/gui.o build/obfuscated/src/gui.o: build/generated/pieces_png.h

build/release/src/%.o: src/%.c
	@mkdir -p $(dir $@)
	$(CC) $(CPPFLAGS) $(RELEASE_CFLAGS) -c $< -o $@

build/obfuscated/src/%.o: src/%.c $(XOLLVM_CLANG)
	@mkdir -p $(dir $@)
	$(XOLLVM_CLANG) $(CPPFLAGS) $(OBF_CFLAGS) $(OBF_DRIVER_FLAGS) -c $< -o $@

build/test/src/%.o: src/%.c
	@mkdir -p $(dir $@)
	$(CC) $(CPPFLAGS) $(BASE_CFLAGS) -O2 -c $< -o $@

build/debug/third_party/chesslib/src/%.o: third_party/chesslib/src/%.c
	@mkdir -p $(dir $@)
	$(CC) $(CPPFLAGS) $(THIRD_CFLAGS) -g -c $< -o $@

build/release/third_party/chesslib/src/%.o: third_party/chesslib/src/%.c
	@mkdir -p $(dir $@)
	$(CC) $(CPPFLAGS) $(THIRD_CFLAGS) -fPIE -DNDEBUG -c $< -o $@

build/test/third_party/chesslib/src/%.o: third_party/chesslib/src/%.c
	@mkdir -p $(dir $@)
	$(CC) $(CPPFLAGS) $(THIRD_CFLAGS) -c $< -o $@

build/test/test_core.o: tests/test_core.c
	@mkdir -p $(dir $@)
	$(CC) $(CPPFLAGS) $(BASE_CFLAGS) -O2 -c $< -o $@

build/test_core: $(TEST_OBJ) build/test/test_core.o
	$(CC) $^ -o $@ -lm

build/obfuscated-test_core: $(OBF_CORE_OBJ) build/test/test_core.o
	$(CC) $^ -o $@ -lm

PYTHON ?= python3

solver:
	$(PYTHON) tools/solve_reference.py flag.enc

test: build/test_core
	$(PYTHON) -m py_compile tools/disassemble_vm.py tools/make_flag.py tools/solve_reference.py
	$(PYTHON) tools/make_flag.py 'flag{test_blue_rose}'
	$(PYTHON) tools/solve_reference.py flag.enc | tail -1 | grep -Fx 'flag{test_blue_rose}'
	./build/test_core
	$(PYTHON) tests/test_consistency.py
	$(PYTHON) tools/make_flag.py 'flag{signals_bloom_between_sixty_four_squares}'

test-obfuscated: obfuscated build/obfuscated-test_core
	$(PYTHON) tools/make_flag.py 'flag{test_blue_rose}'
	./build/obfuscated-test_core
	$(PYTHON) tests/test_consistency.py build/obfuscated-test_core
	$(PYTHON) tools/solve_reference.py flag.enc | tail -1 | grep -Fx 'flag{test_blue_rose}'
	$(PYTHON) tools/make_flag.py 'flag{signals_bloom_between_sixty_four_squares}'

clean:
	$(MAKE) -C $(RAYLIB_DIR) clean
	rm -rf build bluerose bluerose-unstripped bluerose-static bluerose-static-unstripped \
		bluerose-obfuscated bluerose-obfuscated-unstripped bluerose-obfuscated-static \
		Bluerose-x86_64.AppImage
