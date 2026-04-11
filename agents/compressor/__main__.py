"""CLI entry point: python -m agents.compressor"""

from agents.compressor.agent import compressor

if __name__ == "__main__":
    compressor.cli_app(stream=True)
