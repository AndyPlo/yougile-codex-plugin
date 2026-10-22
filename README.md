# YouGile Codex Plugin

An unofficial Codex plugin that connects to the official YouGile MCP server.
Use it to read projects and tasks in Codex and process the results locally.
This repository is not affiliated with YouGile or OpenAI.

The plugin contains configuration only. It does not run a server or require
Node.js, npm, an API key, or an `.env` file. Codex connects directly to YouGile
and handles OAuth authorization and credential storage.

## Requirements and support

- Codex desktop with plugin support and the `codex` CLI available in your terminal.
- A YouGile account with access to the projects you want to use and permission to
  connect an AI assistant. Your company administrator may restrict this permission.
- Git for installation from GitHub or a local clone.

Verified on macOS with Codex CLI **0.163.0**: plugin discovery, OAuth login with
read-only access, and reading data in a Codex chat. Windows, Linux, other MCP
clients, and self-hosted YouGile deployments have not been verified.
The plugin does not guarantee compatibility with every earlier or later Codex version.

## 1. Enable MCP in YouGile

Sign in at [ru.yougile.com/team](https://ru.yougile.com/team/). In your profile,
open **AI assistants (MCP)** and enable access. Keep YouGile open for the
connection approval step.

The documented cloud endpoint is shared:

```text
https://ru.yougile.com/data/ai/mcp
```

You normally do not need to customize it. Each person authorizes their own
account; the URL does not identify an account or grant access to anyone's data.
YouGile's current instructions require the `ru` subdomain for both sign-in and
MCP. See the [official YouGile setup guide](https://help.yougile.com/books/baza-znanii-yougile/page/podkliucenie-mcp-chatgptclaude).

## 2. Install the plugin

Choose **one** installation method.

### From GitHub

```sh
codex plugin marketplace add AndyPlo/yougile-codex-plugin
```

Codex manages the downloaded repository location; a manual clone is unnecessary.
Open **Plugins** in Codex, select **YouGile Local**, and install **YouGile**.
If the source does not appear, restart the desktop app and check again.

On the verified CLI version, you can also install from the terminal:

```sh
codex plugin add yougile@yougile-local
```

The catalog keeps its original name `yougile-local` for compatibility with
existing installations, including when it is downloaded from GitHub.

### From a local clone

Clone into any directory you choose, then run these commands inside that clone:

```sh
git clone https://github.com/AndyPlo/yougile-codex-plugin.git
cd yougile-codex-plugin
codex plugin marketplace add .
```

Install **YouGile** from **Plugins → YouGile Local**, or use the CLI install
command above. All plugin paths are relative to the repository or plugin root;
there is no dependency on a particular username, home directory, or clone name.
Keep the clone available if you use it as the local marketplace source.

## 3. Authorize read-only access

First verify that the installed plugin exposes its MCP server:

```sh
codex mcp get yougile --json
```

The result should show an enabled HTTP server with the official YouGile URL.
Then explicitly start authorization:

```sh
codex mcp login yougile --scopes read
```

Follow the browser flow and approve **read-only** access in YouGile. If the
browser does not open, use the authorization URL printed by the command.
Wait until the terminal reports a successful login before closing it.
Installing the plugin alone does not guarantee that an authorization request
has been started; do not wait for a YouGile notification before running login.

The explicit `--scopes read` matters: an unrestricted login can request both
reading and writing. If installation already started a login, finish or cancel
that flow before starting another one to avoid duplicate approval requests.
The `Read` label in the plugin manifest is descriptive metadata, not an access
control. YouGile enforces the permissions you grant.

## 4. Try it in a new chat

Keep the plugin enabled, start a new Codex chat, and ask:

> List the YouGile projects I can access. Do not change anything.

Then, for example:

> List the tasks on this board and summarize them locally.

Codex reuses saved authorization across chats on the same configured host.
You do not normally approve each new chat. If tools are missing after
installation or an update, restart Codex and open a fresh chat.

## Authorization and plugin lifecycle

- **Disable or enable:** use the plugin switch in Codex. Disabling does not
  revoke OAuth access or erase existing chat history. A fresh chat is the
  clearest way to check the resulting tool availability.
- **Reauthorize:** run `codex mcp login yougile --scopes read` when credentials
  are revoked or can no longer be refreshed. Repeated logins can create
  separate connections in YouGile; review and remove obsolete grants there.
- **Revoke:** remove the connection in YouGile's AI assistant settings.
  Disabling or uninstalling the plugin is not a substitute for revocation.
- **Uninstall:** remove YouGile through Codex Plugins. To remove the catalog
  as well, run `codex plugin marketplace remove yougile-local`.
- **Permissions:** this guide and the verified workflow use read-only access.
  Granting write permissions is a separate decision; writes have not been
  acceptance-tested by this project.

Do not also register the same endpoint using `codex mcp add`. That would create
an independent connection which is not controlled by this plugin's switch.
Credentials belong in Codex's credential storage, never in this repository.
Treat task data saved by an agent as your own local output, not plugin source.

## Updates

For a GitHub marketplace, refresh its repository snapshot:

```sh
codex plugin marketplace upgrade yougile-local
```

For a local clone, obtain the new repository version with Git instead; the
marketplace upgrade command is for Git-backed sources managed by Codex.

Next refresh or reinstall **YouGile** in Codex and restart the app. Codex loads
an installed copy from its own plugin cache; editing a clone or refreshing a
catalog alone is not proof that the installed plugin was updated. Check the
installed version with:

```sh
codex plugin list --marketplace yougile-local --json
```

Do not edit the installed cache by hand. Updating the plugin normally does not
require another login. Reauthorize only if the connection actually requires it.
For reproducible installation, Codex also accepts `--ref` with an existing
Git tag or commit; use only references actually published in this repository.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| `codex` is not found | Make the Codex CLI available on your terminal's PATH. Check `codex --version`. |
| Catalog or plugin is missing | Run `codex plugin marketplace list`, then `codex plugin list --available --marketplace yougile-local --json`. Restart the app if needed. |
| Plugin is installed but server is missing | Run `codex mcp get yougile --json`. Check the installed version, refresh/reinstall, and read the compatibility note below. This happens before OAuth. |
| No approval request in YouGile | Start `codex mcp login yougile --scopes read`; sign in on the `ru` subdomain and check that MCP access is enabled. |
| Login succeeds but tools are absent | Start a new chat; restart Codex if necessary. Plugin discovery and login do not by themselves verify tool loading. |
| Permission denied when reading | Check your YouGile project access, company MCP policy, and whether the OAuth connection was revoked. |
| Multiple YouGile connections | Each login may create a new grant. Keep the intended connection and revoke obsolete ones in YouGile. |

A plain browser GET to the MCP URL may return HTTP 405. An unauthenticated MCP
`initialize` POST returning HTTP 401 with an OAuth challenge can be normal.
Neither response verifies account access or successful tool execution.

### Codex 0.163.0 compatibility

The working package keeps a portable root `plugin.json`, a Codex compatibility
manifest with `mcpServers: "./mcp.json"`, and a minimal HTTP `mcp.json`.
In the tested client, adding `extensions.com.openai.auth` to the server caused
Codex to omit it from the server list. That block is deliberately absent;
HTTP OAuth is the client's default. Do not add it solely to match a newer
schema example without testing server discovery on the supported client.

The root manifest must not introduce `extensions.com.openai` casually: an
inline OpenAI overlay replaces the compatibility overlay rather than merging
with it. Preserve and test the MCP file reference when changing packaging.

## Repository layout

```text
.agents/plugins/marketplace.json       Marketplace catalog
plugins/yougile/plugin.json            Portable identity and metadata
plugins/yougile/.codex-plugin/plugin.json
                                      Codex compatibility manifest
plugins/yougile/mcp.json                Official HTTP endpoint
scripts/validate.py                   Optional maintainer validation
CHANGELOG.md                          Version history
LICENSE                               MIT license for this repository
```

## Maintainer checks

Python 3.9+ is needed only for the optional validation script, not to use the plugin.

```sh
python3 scripts/validate.py
python3 scripts/validate.py --codex
```

The first command validates package paths, identities, and the minimal MCP
configuration. The second also copies the package into a temporary path with
spaces, uses a separate temporary `CODEX_HOME`, installs through the real Codex
CLI, and verifies the server after moving the source away. It does not start
OAuth, read tasks, or modify your normal Codex configuration or installed plugin.

Before a release, update both manifest versions and the changelog. Recheck the
GitHub installation route after pushing; local checks cannot prove that
unpublished files are available from GitHub. Perform an explicit read-only live
check separately when needed; do not grant write access just to test packaging.

## References and license

- [Codex plugin packaging](https://developers.openai.com/plugins/build/plugins)
- [Codex MCP and OAuth](https://developers.openai.com/codex/mcp)
- [YouGile MCP setup](https://help.yougile.com/books/baza-znanii-yougile/page/podkliucenie-mcp-chatgptclaude)

Licensed under [MIT](LICENSE). This license covers this repository, not the
YouGile service, its data, or third-party trademarks.
