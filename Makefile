PROGRAM      ?= mince
SOURCE       ?= mince
PYTHON       ?= python3
SUDO         ?= sudo

USER_PREFIX  := $(HOME)/.local
USER_DIR     := $(USER_PREFIX)/share/$(PROGRAM)
USER_BIN     := $(USER_PREFIX)/bin
USER_LAUNCH  := $(USER_BIN)/$(PROGRAM)
USER_VENV    := $(USER_DIR)/.venv

GLOBAL_DIR   := /opt/$(PROGRAM)
GLOBAL_BIN   := /usr/local/bin
GLOBAL_LAUNCH:= $(GLOBAL_BIN)/$(PROGRAM)
GLOBAL_VENV  := $(GLOBAL_DIR)/.venv

ifeq ($(shell id -u),0)
SUDO :=
endif

.PHONY: install-user uninstall-user update-user install-global uninstall-global update-global update help shell

help:
	@printf '%s\n' \
	  'Targets:' \
	  '  install-user      Install to ~/.local/share/mince and ~/.local/bin/mince' \
	  '  uninstall-user    Remove the user install' \
	  '  update-user       Refresh the user install' \
	  '  install-global    Install to /opt/mince and /usr/local/bin/mince' \
	  '  uninstall-global  Remove the global install' \
	  '  update-global     Refresh the global install' \
	  '  update            Auto-detect and update whichever install exists' \
	  '  shell             Start a shell in the installed environment'

install-user:
	@set -eu; \
	mkdir -p "$(USER_PREFIX)/share" "$(USER_BIN)"; \
	if [ -d "$(USER_DIR)" ]; then \
		echo "$(USER_DIR) already exists; reusing it"; \
	else \
		mkdir -p "$(USER_DIR)"; \
	fi; \
	cp -f "$(SOURCE)" "$(USER_DIR)/$(PROGRAM)"; \
	chmod 755 "$(USER_DIR)/$(PROGRAM)"; \
	if [ ! -x "$(USER_VENV)/bin/python" ]; then \
		"$(PYTHON)" -m venv "$(USER_VENV)"; \
	fi; \
	"$(USER_VENV)/bin/python" -m pip install -r requirements.txt; \
	printf '%s\n' '#!/bin/sh' 'exec "$(USER_VENV)/bin/python" "$(USER_DIR)/$(PROGRAM)" "$$@"' > "$(USER_LAUNCH)"; \
	chmod 755 "$(USER_LAUNCH)"

uninstall-user:
	@rm -f "$(USER_LAUNCH)"; \
	rm -rf "$(USER_DIR)"; \
	rm -rf "$(HOME)/.local/state/$(PROGRAM)"

update-user:
	@set -eu; \
	if [ ! -d "$(USER_DIR)" ]; then \
		echo "User install not found; running install-user"; \
		$(MAKE) install-user; \
	else \
		cp -f "$(SOURCE)" "$(USER_DIR)/$(PROGRAM)"; \
		chmod 755 "$(USER_DIR)/$(PROGRAM)"; \
		if [ ! -x "$(USER_VENV)/bin/python" ]; then \
			"$(PYTHON)" -m venv "$(USER_VENV)"; \
		fi; \
		"$(USER_VENV)/bin/python" -m pip install --upgrade pip openai tiktoken; \
		printf '%s\n' '#!/bin/sh' 'exec "$(USER_VENV)/bin/python" "$(USER_DIR)/$(PROGRAM)" "$$@"' > "$(USER_LAUNCH)"; \
		chmod 755 "$(USER_LAUNCH)"; \
	fi

install-global:
	@set -eu; \
	$(SUDO) mkdir -p "$(GLOBAL_DIR)" "$(GLOBAL_BIN)"; \
	if [ -d "$(GLOBAL_DIR)" ]; then \
		echo "$(GLOBAL_DIR) already exists; reusing it"; \
	fi; \
	$(SUDO) cp -f "$(SOURCE)" "$(GLOBAL_DIR)/$(PROGRAM)"; \
	$(SUDO) chmod 755 "$(GLOBAL_DIR)/$(PROGRAM)"; \
	if [ ! -x "$(GLOBAL_VENV)/bin/python" ]; then \
		$(SUDO) "$(PYTHON)" -m venv "$(GLOBAL_VENV)"; \
	fi; \
	$(SUDO) "$(GLOBAL_VENV)/bin/python" -m pip install -r requirements.txt; \
	printf '%s\n' '#!/bin/sh' 'exec "$(GLOBAL_VENV)/bin/python" "$(GLOBAL_DIR)/$(PROGRAM)" "$$@"' | $(SUDO) tee "$(GLOBAL_LAUNCH)" >/dev/null; \
	$(SUDO) chmod 755 "$(GLOBAL_LAUNCH)"

uninstall-global:
	@$(SUDO) rm -f "$(GLOBAL_LAUNCH)"; \
	$(SUDO) rm -rf "$(GLOBAL_DIR)"; \
	rm -rf "$(HOME)/.local/state/$(PROGRAM)"

update-global:
	@set -eu; \
	if [ ! -d "$(GLOBAL_DIR)" ]; then \
		echo "Global install not found; running install-global"; \
		$(MAKE) install-global; \
	else \
		$(SUDO) cp -f "$(SOURCE)" "$(GLOBAL_DIR)/$(PROGRAM)"; \
		$(SUDO) chmod 755 "$(GLOBAL_DIR)/$(PROGRAM)"; \
		if [ ! -x "$(GLOBAL_VENV)/bin/python" ]; then \
			$(SUDO) "$(PYTHON)" -m venv "$(GLOBAL_VENV)"; \
		fi; \
		$(SUDO) "$(GLOBAL_VENV)/bin/python" -m pip install --upgrade pip openai tiktoken; \
		printf '%s\n' '#!/bin/sh' 'exec "$(GLOBAL_VENV)/bin/python" "$(GLOBAL_DIR)/$(PROGRAM)" "$$@"' | $(SUDO) tee "$(GLOBAL_LAUNCH)" >/dev/null; \
		$(SUDO) chmod 755 "$(GLOBAL_LAUNCH)"; \
	fi

install: install-user

update:
	@set -eu; \
	if [ -d "$(GLOBAL_DIR)" ]; then \
		$(MAKE) update-global; \
	elif [ -d "$(USER_DIR)" ]; then \
		$(MAKE) update-user; \
	else \
		echo "No install found; run install-user or install-global"; \
		exit 1; \
	fi

shell:
	@set -eu; \
	if [ -d "$(GLOBAL_DIR)" ]; then \
		bash --init-file "$(GLOBAL_VENV)/bin/activate"; \
	elif [ -d "$(USER_DIR)" ]; then \
		bash --init-file "$(USER_VENV)/bin/activate"; \
	else \
		echo "No install found; run install-user or install-global"; \
		exit 1; \
	fi

