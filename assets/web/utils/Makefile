# Makefile for ADT Manual Autocuidados
# Handles chat editor repository setup and execution

.PHONY: help setup-chat-editor run-creator stop

# Default target
help:
	@echo "Available targets:"
	@echo "  setup-chat-editor  - Set up the chat editor repository"
	@echo "  run-creator        - Run the chat editor creator"
	@echo "  stop               - Stop the running chat editor"
	@echo "  help               - Show this help message"

# Ask for chat editor path and set it up
setup-chat-editor:
	@echo "Please provide the path to the chat editor repository."
	@echo "If you don't have it, leave it blank and it will be cloned automatically."
	@bash -c 'read -p "Chat editor path (or press Enter to clone): " chat_editor_path; \
	if [ -z "$$chat_editor_path" ]; then \
		echo "No path provided. Checking for existing chat editor repository..."; \
		cd .. && \
		if [ ! -d "adt-chat-editor" ]; then \
			echo "Chat editor repository not found. Cloning..."; \
			git clone git@github.com:unicef/adt-chat-editor.git; \
			echo "Chat editor repository cloned successfully."; \
		else \
			echo "Chat editor repository already exists. Updating..."; \
			cd adt-chat-editor && \
			git pull && \
			cd ..; \
		fi; \
		cd adt-chat-editor && \
		echo "Chat editor repository is ready at: $$(pwd)"; \
	else \
		expanded_path=$$(eval echo "$$chat_editor_path"); \
		if [ -d "$$expanded_path" ]; then \
			echo "Using existing chat editor at: $$expanded_path"; \
			cd "$$expanded_path"; \
		else \
			echo "Error: Directory $$expanded_path does not exist."; \
			exit 1; \
		fi; \
	fi'

# Run the creator command in the chat editor directory
run-creator:
	@echo "Please provide the path to the chat editor repository."
	@echo "If you don't have it, leave it blank and it will be cloned automatically."
	@bash -c 'read -p "Chat editor path (or press Enter to clone): " chat_editor_path; \
	if [ -z "$$chat_editor_path" ]; then \
		echo "No path provided. Checking for existing chat editor repository..."; \
		cd .. && \
		if [ ! -d "adt-chat-editor" ]; then \
			echo "Chat editor repository not found. Cloning..."; \
			git clone git@github.com:unicef/adt-chat-editor.git; \
			echo "Chat editor repository cloned successfully."; \
		else \
			echo "Chat editor repository already exists. Updating..."; \
			cd adt-chat-editor && \
			git pull && \
			cd ..; \
		fi; \
		cd adt-chat-editor && \
		echo "Chat editor repository is ready at: $$(pwd)"; \
		echo "$$(pwd)" > .chat-editor-path; \
		echo "Starting chat editor application..."; \
		make creator REPO_PATH=$(shell pwd); \
	else \
		expanded_path=$$(eval echo "$$chat_editor_path"); \
		if [ -d "$$expanded_path" ]; then \
			echo "Using existing chat editor at: $$expanded_path"; \
			echo "$$expanded_path" > .chat-editor-path; \
			cd "$$expanded_path"; \
			echo "Starting chat editor application..."; \
			make creator REPO_PATH=$(shell pwd); \
		else \
			echo "Error: Directory $$expanded_path does not exist."; \
			exit 1; \
		fi; \
	fi'

# Stop the running chat editor
stop:
	@if [ -f ".chat-editor-path" ]; then \
		chat_editor_path=$$(cat .chat-editor-path); \
		echo "Using saved chat editor path: $$chat_editor_path"; \
		if [ -d "$$chat_editor_path" ]; then \
			cd "$$chat_editor_path"; \
			echo "Stopping chat editor application..."; \
			make stop 2>/dev/null || docker-compose down || echo "No running containers found."; \
		else \
			echo "Error: Saved chat editor path does not exist: $$chat_editor_path"; \
			echo "Please run 'make run-creator' first to set up the chat editor."; \
			exit 1; \
		fi; \
	else \
		echo "No saved chat editor path found."; \
		echo "Please run 'make run-creator' first to set up the chat editor."; \
		exit 1; \
	fi

# Convenience target to do everything
all: run-creator 