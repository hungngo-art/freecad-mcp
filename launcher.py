"""FreeCAD MCP single-EXE launcher: stdio server and Antigravity management CLI."""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

NAME = "freecad-mcp"
KEY = "freecad"
START = "<!-- freecad-mcp:begin -->"
STOP = "<!-- freecad-mcp:end -->"
GUIDANCE = """## FreeCAD MCP
Use the \`freecad\` MCP tools for parametric FreeCAD operations. Start FreeCAD
and enable its FreeCADMCP workbench RPC server first. DXF export requires a
2D projection; DWG requires a separate converter and should be validated.
"""

def paths():
    home = Path.home()
    gemini = home / ".gemini"
    return {
        "config": gemini / "config" / "mcp_config.json",
        "state": gemini / "config" / "freecad-mcp-managed.json",
        "instructions": gemini / "AGENTS.md",
        "skill": home / ".agents" / "skills" / NAME,
        "gemini_skill": gemini / "config" / "skills" / NAME,
        "addon": Path(os.environ.get("APPDATA", str(home / "AppData" / "Roaming")))
                 / "FreeCAD" / "Mod" / "FreeCADMCP",
    }

def resource(path):
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return root / path

def exe_path():
    return str(Path(sys.executable if getattr(sys, "frozen", False) else __file__).resolve())

def read_json(path):
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value

def write_text(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".freecad-mcp-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def write_json(path, value):
    write_text(path, json.dumps(value, indent=2, ensure_ascii=False) + "\n")

def managed(path):
    return (path / ".freecad-mcp-managed").is_file()

def install():
    p = paths()
    command = exe_path()
    config = read_json(p["config"])
    servers = config.setdefault("mcpServers", {})
    if not isinstance(servers, dict):
        raise ValueError("mcpServers is not a JSON object")
    state = read_json(p["state"])
    previous = state.get("exe")
    existing = servers.get(KEY)
    allowed = [{"command": command, "args": []}]
    if previous and state.get("key") == KEY:
        allowed.append({"command": previous, "args": []})
    if existing is not None and existing not in allowed:
        raise RuntimeError("A non-managed 'freecad' MCP entry already exists; no changes made")
    for k in ("skill", "gemini_skill"):
        if p[k].exists() and not managed(p[k]):
            raise RuntimeError(f"Refusing to overwrite existing skill: {p[k]}")
    skill_src = resource("resources/SKILL.md")
    addon_src = resource("addon/FreeCADMCP")
    if not skill_src.is_file() or not addon_src.is_dir():
        raise FileNotFoundError("Bundled skill/addon is missing; rebuild the executable")
    instructions = p["instructions"]
    original = instructions.read_text(encoding="utf-8") if instructions.exists() else ""
    if (START in original) != (STOP in original):
        raise RuntimeError("Global AGENTS.md contains incomplete installer markers")
    for k in ("skill", "gemini_skill"):
        p[k].mkdir(parents=True, exist_ok=True)
        shutil.copyfile(skill_src, p[k] / "SKILL.md")
        (p[k] / ".freecad-mcp-managed").write_text("freecad-mcp\n", encoding="utf-8")
    if START not in original:
        write_text(instructions, original.rstrip("\n") + "\n\n" + START + "\n" + GUIDANCE + STOP + "\n")
    if p["addon"].exists() and not managed(p["addon"]):
        print("Existing FreeCADMCP addon preserved (not owned by this installer).")
    else:
        if p["addon"].exists():
            shutil.rmtree(p["addon"])
        p["addon"].parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(addon_src, p["addon"])
        (p["addon"] / ".freecad-mcp-managed").write_text("freecad-mcp\n", encoding="utf-8")
    servers[KEY] = {"command": command, "args": []}
    write_json(p["config"], config)
    write_json(p["state"], {"key": KEY, "exe": command})
    print(f"Installed Antigravity MCP registration: {p['config']}")
    print("Restart FreeCAD, start FreeCADMCP RPC server, and refresh Antigravity.")
    return 0

def uninstall():
    p = paths()
    state = read_json(p["state"])
    config = read_json(p["config"])
    servers = config.get("mcpServers")
    if isinstance(servers, dict) and state.get("key") == KEY:
        if servers.get(KEY) == {"command": state.get("exe"), "args": []}:
            del servers[KEY]
            write_json(p["config"], config)
        elif KEY in servers:
            print("The MCP registration was modified: preserving it.")
    instructions = p["instructions"]
    if instructions.exists():
        txt = instructions.read_text(encoding="utf-8")
        if START in txt and STOP in txt:
            a = txt.index(START)
            b = txt.index(STOP, a) + len(STOP)
            write_text(instructions, txt[:a] + txt[b:])
    for k in ("skill", "gemini_skill", "addon"):
        if managed(p[k]):
            shutil.rmtree(p[k])
    p["state"].unlink(missing_ok=True)
    print("Removed installer-managed Antigravity files and registration.")
    return 0

def check():
    p = paths()
    state = read_json(p["state"])
    config = read_json(p["config"])
    servers = config.get("mcpServers", {})
    current = servers.get(KEY) if isinstance(servers, dict) else None
    command = state.get("exe", exe_path())
    status = {
        "MCP registration": state.get("key") == KEY and current == {"command": command, "args": []},
        "EXE file": Path(command).is_file(),
        "Global agents skill": managed(p["skill"]) and (p["skill"] / "SKILL.md").is_file(),
        "Antigravity skill": managed(p["gemini_skill"]) and (p["gemini_skill"] / "SKILL.md").is_file(),
        "Global instructions": p["instructions"].is_file()
             and START in p["instructions"].read_text(encoding="utf-8")
             and STOP in p["instructions"].read_text(encoding="utf-8"),
        "FreeCAD addon": p["addon"].is_dir(),
    }
    for label, ok in status.items():
        print(f"{'OK' if ok else 'MISSING'}: {label}")
    print("Note: this check does not verify the running FreeCAD RPC connection.")
    return 0 if all(status.values()) else 1

def usage():
    print("FreeCAD MCP for Antigravity - standalone Windows EXE")
    print("Usage: freecad-mcp.exe [help|install|uninstall|check]")
    print("  help       Display help")
    print("  install    Install addon and skill; register MCP and instructions")
    print("  uninstall  Remove managed registration, addon, skill and instructions")
    print("  check      Check Antigravity integration (exit status 0=ready, 1=missing)")
    print("  (none)     Run the original MCP stdio server")
    return 0

def main():
    args = sys.argv[1:]
    command = args[0].lower() if args else ""
    actions = {"help": usage, "--help": usage, "-h": usage,
               "install": install, "uninstall": uninstall, "check": check}
    if command in actions:
        if len(args) != 1:
            print(f"Unexpected extra arguments: {args[1:]}", file=sys.stderr)
            return 2
        try:
            return actions[command]()
        except (OSError, ValueError, RuntimeError) as error:
            print(f"Error: {error}", file=sys.stderr)
            return 2
    if command and not command.startswith("-"):
        print(f"Unknown command: {command}. Use help.", file=sys.stderr)
        return 2
    from freecad_mcp.server import main as server_main
    server_main()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
