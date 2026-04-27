#!/bin/bash
cd "$(dirname "$0")"

# uv がなければインストール
command -v uv >/dev/null 2>&1 || {
    echo "uv をインストールしています..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
}

# uvx で起動
uvx --from . phone-automation
