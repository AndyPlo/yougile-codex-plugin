#!/usr/bin/env python3
"""Validate the package, optionally using an isolated Codex CLI installation."""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def package_path(root, value):
    require(isinstance(value, str) and value.startswith("./"),
            "Package paths must start with ./")
    resolved = (root / value).resolve()
    require(root.resolve() in resolved.parents, "Package path escapes its root")
    require(resolved.exists(), f"Missing package path: {value}")
    return resolved


def validate(root):
    catalog = read_json(root / ".agents/plugins/marketplace.json")
    require(catalog["name"] == "yougile-local", "Marketplace identity changed")
    require(len(catalog["plugins"]) == 1, "Expected one plugin")
    entry = catalog["plugins"][0]
    require(entry["source"]["source"] == "local", "Expected repository-local source")
    plugin = package_path(root, entry["source"]["path"])
    portable = read_json(plugin / "plugin.json")
    compat = read_json(plugin / ".codex-plugin/plugin.json")
    require(entry["name"] == portable["name"] == compat["name"] == "yougile",
            "Plugin identities do not match")
    require(portable["version"] == compat["version"], "Manifest versions differ")
    require("com.openai" not in portable.get("extensions", {}),
            "Inline OpenAI metadata would replace the compatibility overlay")
    mcp = read_json(package_path(plugin, compat["mcpServers"]))
    require(set(mcp["mcpServers"]) == {"yougile"}, "Unexpected MCP servers")
    require(mcp["mcpServers"]["yougile"] == {
        "type": "streamable-http",
        "url": "https://ru.yougile.com/data/ai/mcp",
    }, "Expected minimal official HTTP endpoint without auth extensions or secrets")
    require(portable["license"] == "MIT" and (root / "LICENSE").is_file(),
            "MIT metadata and license file are required")
    return portable["version"]


def check_codex(root, version):
    executable = shutil.which("codex")
    require(executable is not None, "codex is not on PATH")
    # All Codex writes are directed to this disposable home. Never run login.
    with tempfile.TemporaryDirectory(prefix="yougile plugin check ") as directory:
        temp = Path(directory)
        source = temp / "marketplace with spaces"
        for name in (".agents", "plugins"):
            shutil.copytree(root / name, source / name)
        home = temp / "codex home"
        home.mkdir()
        env = {**os.environ, "CODEX_HOME": str(home)}

        def run(*args):
            result = subprocess.run(
                [executable, *args], cwd=temp, env=env,
                capture_output=True, text=True, timeout=45,
            )
            require(result.returncode == 0,
                    f"codex {' '.join(args)} failed:\n{result.stderr}\n{result.stdout}")
            return result.stdout

        print(run("--version").strip())
        run("plugin", "marketplace", "add", str(source))
        run("plugin", "add", "yougile@yougile-local", "--json")
        installed = read_json_output(run(
            "plugin", "list", "--marketplace", "yougile-local", "--json"
        ))["installed"]
        require(any(p["name"] == "yougile" and p["version"] == version
                    and p["enabled"] for p in installed),
                "Expected installed, enabled plugin version was not found")
        # Moving the original source catches accidental references outside the cache.
        source.rename(temp / "source moved away")
        server = read_json_output(run("mcp", "get", "yougile", "--json"))
        require(server["enabled"], "Server is disabled")
        require(server["transport"]["type"] == "streamable_http",
                "HTTP transport was not loaded")
        require(server["transport"]["url"] == "https://ru.yougile.com/data/ai/mcp",
                "Unexpected installed endpoint")
        print("PASS: real CLI installation, paths with spaces, and cached MCP discovery")


def read_json_output(value):
    return json.loads(value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex", action="store_true",
                        help="also install and inspect using a temporary CODEX_HOME")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    version = validate(root)
    print(f"PASS: package paths, identities, version {version}, and MCP configuration")
    if args.codex:
        check_codex(root, version)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, subprocess.TimeoutExpired) as error:
        raise SystemExit(f"FAIL: {error}") from error
