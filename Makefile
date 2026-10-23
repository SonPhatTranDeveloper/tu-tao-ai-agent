# Agent ReAct — chạy bằng: make run
# Cần ANTHROPIC_API_KEY trong môi trường:
#   export ANTHROPIC_API_KEY=sk-ant-...

.PHONY: run help

run:
	@test -n "$$ANTHROPIC_API_KEY" || { \
	  echo "Thiếu ANTHROPIC_API_KEY."; \
	  echo "Chạy: export ANTHROPIC_API_KEY=sk-ant-..."; \
	  exit 1; }
	@uv run --quiet --with anthropic python agent.py

help:
	@echo "make run   — chạy agent (cần ANTHROPIC_API_KEY)"
