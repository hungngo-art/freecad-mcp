---
name: freecad-mcp
description: Use FreeCAD through its local MCP server to create, inspect, edit, and export parametric CAD models and 2D drawings.
---

# FreeCAD MCP

For CAD tasks, prefer the tools provided by the \`freecad\` MCP server.
Ensure FreeCAD is installed and open, the FreeCADMCP workbench is loaded, and
the RPC server in FreeCAD is started.

## Workflow

1. Inspect documents and parameters before changing a model.
2. Create/edit parametric geometry using native FreeCAD objects.
3. Recompute and inspect the resulting document.
4. Save the native .FCStd project before exporting.
5. For DXF, generate the correct 2D shape or projection first, then export.
6. For DWG, use a separate supported converter and validate the output in a CAD application.

Do not claim full AutoCAD DWG compatibility, and do not delete user CAD data
unless explicitly asked. If FreeCAD's RPC connection is unavailable,
explain how to start the addon.
