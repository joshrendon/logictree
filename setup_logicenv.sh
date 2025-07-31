#!/bin/bash

echo "Creating virtual environment in ./logicenv"
python3 -m venv logicenv
source logicenv/bin/activate

echo "Upgrading pip and installing core dependencies"
pip install --upgrade pip
pip install flask jinja2 antlr4-python3-runtime graphviz

echo "Freezing installed packages to requirements.txt"
pip freeze > requirements.txt

echo "Setup complete."
echo "To activate this environment in the future, run:"
echo "  source logicenv/bin/activate"

