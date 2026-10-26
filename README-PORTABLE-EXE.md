# FreeCAD MCP Windows single EXE for Google Antigravity

GitHub Actions (Node.js 24 + actions @v6, Python 3.12 build) creates a **single**
dist/freecad-mcp.exe using PyInstaller. Python and uv are **not required on
the end user's Windows computer**. FreeCAD itself remains required.

Actions workflow: .github/workflows/build-windows-exe.yml
Actions artifact name: freecad-mcp-windows-x64 (contains one EXE)

## Windows commands

Run the executable from an ordinary PowerShell terminal:

    .\freecad-mcp.exe help
    .\freecad-mcp.exe install
    .\freecad-mcp.exe check
    .\freecad-mcp.exe uninstall

Invoking the EXE with no arguments runs the original stdio MCP server.
"install" saves the absolute executable path to
~/.gemini/config/mcp_config.json under "mcpServers.freecad"; keep it at that
path or rerun install after moving it. The installer embeds the FreeCAD addon,
installs global skills in ~/.agents/skills/freecad-mcp and
~/.gemini/config/skills/freecad-mcp, and the Antigravity CLI global path
~/.gemini/antigravity-cli/skills/freecad-mcp; it also adds marked instructions to
~/.gemini/AGENTS.md.

Empty MCP JSON files are initialized as new objects; malformed non-empty JSON
files are rejected with a descriptive error and never overwritten.

The installer preserves unrelated configuration entries and refuses to
overwrite an existing, unrelated "freecad" MCP server, user skill or addon.
Uninstall removes installer-managed materials only.

After installation, launch FreeCAD and start its FreeCADMCP RPC server. Then
refresh MCP servers in Google Antigravity. The check command only validates
local installation state, not a live RPC connection or the presence of FreeCAD.

Security: the original MCP server exposes remote CAD Python execution tools.
Keep FreeCAD RPC local and authorize only agents you trust.
