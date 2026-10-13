# --- Settings ---
COMPOSE   ?= docker compose
# UI language: en (default) or ru.
UI_LANG   ?= en
export UI_LANG
CONTAINER_TYPE = $(if $(DEV),dev,build)
ZMK_IMAGE ?= $(shell python3 scripts/select_image.py --container $(CONTAINER_TYPE))

HELP_COLOR = \033[36m
RESET_COLOR = \033[0m

# Localized message lookup for the active UI_LANG (ru or en).
msg = $(MSG_$(1)_$(if $(filter ru,$(UI_LANG)),ru,en))

MSG_usage_en   := Usage:
MSG_usage_ru   := Использование:
MSG_targets_en := Targets:
MSG_targets_ru := Цели:
MSG_arg_en     := <target>
MSG_arg_ru     := <цель>
MSG_build_en   := 🔨 Building in the "$(CONTAINER_TYPE)" container...
MSG_build_ru   := 🔨 Сборка в контейнере "$(CONTAINER_TYPE)"...
MSG_update_en  := 🔄 Updating dependencies in the "$(CONTAINER_TYPE)" container...
MSG_update_ru  := 🔄 Обновление зависимостей в "$(CONTAINER_TYPE)"...
MSG_shell_en   := 🐚 Starting a shell in the "$(CONTAINER_TYPE)" container...
MSG_shell_ru   := 🐚 Запуск оболочки в контейнере "$(CONTAINER_TYPE)"...
MSG_clean_en   := 🧹 Cleaning the output directory...
MSG_clean_ru   := 🧹 Очистка содержимого output...

default: help

.PHONY: preflight
preflight:
	@python3 scripts/check_config.py

.PHONY: build
build: preflight ## 🔨 Build the firmware (make build DEV=1 — in the dev image) :: 🔨 Собрать прошивку (make build DEV=1 — в dev-образе)
	@echo '$(call msg,build)'
	@ZMK_IMAGE=$(ZMK_IMAGE) $(COMPOSE) run --rm -e UI_LANG=$(UI_LANG) zmk-build

.PHONY: update
update: preflight ## 🔄 Update west dependencies (make update DEV=1 — in the dev image) :: 🔄 Обновить west-зависимости (make update DEV=1 — в dev-образе)
	@echo '$(call msg,update)'
	@ZMK_IMAGE=$(ZMK_IMAGE) $(COMPOSE) run --rm -e UI_LANG=$(UI_LANG) -e ZMK_UPDATE=1 zmk-build

.PHONY: shell
shell: ## 🐚 Open a shell in the selected image :: 🐚 Открыть оболочку в выбранном образе
	@echo '$(call msg,shell)'
	@ZMK_IMAGE=$(ZMK_IMAGE) $(COMPOSE) run --rm --entrypoint bash zmk-build

.PHONY: clean
clean: ## 🧹 Clean the output directory (keeps the workspace) :: 🧹 Очистить содержимое папки output (workspace не трогает)
	@echo '$(call msg,clean)'
	@mkdir -p output
	@find output -mindepth 1 -delete 2>/dev/null || true

.PHONY: help
help: ## 📖 Show this help :: 📖 Показать справку
	@awk -v col="$(HELP_COLOR)" -v res="$(RESET_COLOR)" \
		-v usage="$(call msg,usage)" -v targets="$(call msg,targets)" \
		-v arg="$(call msg,arg)" -v lang="$(if $(filter ru,$(UI_LANG)),ru,en)" \
		'BEGIN { \
		FS = ":.*##"; \
		printf "%s\n  make %s%s%s\n\n%s\n", usage, col, arg, res, targets \
	} \
	/^[a-zA-Z_-]+:.*##/ { \
		count++; \
		names[count] = $$1; \
		split($$2, parts, " *:: *"); \
		help[$$1] = (lang == "ru" && parts[2] != "") ? parts[2] : parts[1]; \
		if (length($$1) > max_len) max_len = length($$1); \
	} \
	END { \
		for (i = 1; i <= count; i++) { \
			tname = names[i]; \
			printf "  %s%-*s%s  %s\n", col, max_len, tname, res, help[tname] \
		} \
	}' $(MAKEFILE_LIST)
