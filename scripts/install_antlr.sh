#!/usr/bin/env bash

# Exit on any error
set -e

# Constants
ANTLR_VERSION="4.13.1"
ANTLR_JAR="antlr-${ANTLR_VERSION}-complete.jar"
INSTALL_DIR="${HOME}/.local/bin"
JAR_PATH="${INSTALL_DIR}/${ANTLR_JAR}"

# Ensure install dir exists
mkdir -p "$INSTALL_DIR"

# Download ANTLR if not present
if [ ! -f "$JAR_PATH" ]; then
  echo "🔽 Downloading ANTLR ${ANTLR_VERSION} to ${JAR_PATH}..."
  curl -L -o "$JAR_PATH" "https://www.antlr.org/download/${ANTLR_JAR}"
else
  echo "✅ ANTLR JAR already exists at ${JAR_PATH}"
fi

# Create wrapper script for invoking ANTLR
ANTLR_CMD="${INSTALL_DIR}/antlr4"
cat > "$ANTLR_CMD" <<EOF
#!/usr/bin/env bash
java -Xmx500M -cp "${JAR_PATH}:\$CLASSPATH" org.antlr.v4.Tool "\$@"
EOF
chmod +x "$ANTLR_CMD"

# Optional: add `grun` (test rig) script too
GRUN_CMD="${INSTALL_DIR}/grun"
cat > "$GRUN_CMD" <<EOF
#!/usr/bin/env bash
java -cp "${JAR_PATH}:\$CLASSPATH" org.antlr.v4.gui.TestRig "\$@"
EOF
chmod +x "$GRUN_CMD"

echo "✅ ANTLR install complete."
echo "➕ Add ~/.local/bin to your PATH if it's not already:"
echo '    export PATH="$HOME/.local/bin:$PATH"'
