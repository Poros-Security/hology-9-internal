SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c
.ONESHELL:

.PHONY: help appimage verify clean development

help:
	@echo 'STELLAR build targets:'
	@echo '  make appimage     Build release/STELLAR.AppImage (requires STELLAR_FLAG)'
	@echo '  make verify       Extract and verify the finished AppImage'
	@echo '  make development  Build an unstripped local development executable'
	@echo '  make clean        Remove generated release artifacts only'

appimage:
	: "$${STELLAR_FLAG:?Set STELLAR_FLAG to the production HOLOGY9 flag}"
	case "$$STELLAR_FLAG" in HOLOGY9\{*\}) ;; *) echo 'STELLAR_FLAG has invalid format' >&2; exit 1;; esac
	if [[ "$$STELLAR_FLAG" == 'HOLOGY9{Fake_flag_dont_submit}' ]]; then
	  echo 'refusing to produce a release with the development flag' >&2
	  exit 1
	fi
	./scripts/clean-release.sh
	cargo run --locked --release -p midnight-builder -- app/src/assets/gifs
	unset STELLAR_FLAG
	./scripts/build-appimage-container.sh
	install -Dm644 challenge/challenge.txt release/challenge.txt
	./scripts/verify-appimage.sh

verify:
	./scripts/verify-appimage.sh

development:
	./scripts/build-development.sh

clean:
	./scripts/clean-release.sh
