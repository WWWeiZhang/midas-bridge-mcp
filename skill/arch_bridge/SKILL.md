---
name: midas-civil-bridge-modeling
description: >
  Use this skill whenever the user wants to build, create, or model a bridge or structural
  model in Midas Civil using MCP tools — including beam bridges, arch bridges, truss bridges,
  cable-stayed bridges, or any structural frame. Also use it when the user asks about Midas
  Civil MCP operations, load application, boundary conditions, or analysis workflow. This skill
  covers the complete pipeline: geometry → materials/sections → elements → supports →
  releases → loads → analysis → results. Even if the user doesn't explicitly mention
  "Midas" or "bridge", if they describe a structural model with nodes, elements, and loads
  in the context of this project, trigger this skill.
---

# Midas Civil MCP Bridge Modeling

Complete workflow for building bridge and structural FEM models via Midas Civil MCP tools.

## Prerequisites

Before any modeling, verify the MCP server is connected:
- Check `.mcp.json` exists in project root with `type: "stdio"`, correct `command` (absolute path to `.venv/Scripts/python.exe`), and `PYTHONPATH=src` in env
- Check `enableAllProjectMcpServers: true` in Claude Code settings
- If tools 404: restart Claude Code session to reload the MCP server

## Unit System Warning

Midas Civil default unit is **tonf + m**. When the user specifies "kN and m", note that:
- All force inputs (loads, material E) will be interpreted as tonf unless the unit system is changed
- To convert: 1 tonf ≈ 9.81 kN. Input force values must be divided by 9.81 if the user means kN
- Reaction and force outputs are in tonf; displacements in meters
- Currently no MCP tool to change unit system — mention this to the user upfront

## Modeling Workflow (Must Follow This Order)

### 1. Geometry Design (internal, not sent to Midas)

Before creating any nodes, design the geometry:
- Define coordinate system: usually X=longitudinal, Y=transverse, Z=vertical
- For arch bridges: parabolic formula `z(x) = 4*h*x*(L-x)/L²`
- Number nodes sequentially: group them (girder_left=1..11, girder_right=12..22, arch_left=23..33, etc.)
- Keep a clear mental map or scratch notes of node IDs for element creation

### 2. Create Nodes

Use `create_nodes` with all nodes in a single list (accepts large batches):
```json
[{"id":1,"x":0,"y":0,"z":0}, {"id":2,"x":5,"y":0,"z":0}, ...]
```
- IDs must be unique positive integers
- Coordinates in meters
- Batch all nodes into ONE call for efficiency

### 3. Create Materials

Try database materials first (`create_steel_material` / `create_concrete_material`):
- A36 → standard="ASTM(S)", db_name="A36"
- Q345 → standard="GB(S)", db_name="Q345"

If database lookup fails (error 400), **immediately fallback** to `create_user_steel_material`:
- Q345/A36: E=200,000,000 kPa, ν=0.3, density=78.5 kN/m³, mass_density=7.85 ton/m³
- A572-50: E=200,000,000 kPa, ν=0.3, density=78.5 kN/m³, mass_density=7.85 ton/m³
- C30/C40 concrete: E=30,000,000 kPa, ν=0.2, density=25 kN/m³, mass_density=2.5 ton/m³

### 4. Create Sections

Use `create_solid_rectangle_section` for quick modeling. Name them clearly:
- Main Girder: 0.5×2.0m (large box girder)
- Cross Beam: 0.3×0.8m
- Arch Rib: 0.8×1.2m
- Hanger: 0.08×0.08m (small tension-only rod)
- Strut: 0.3×0.3m
- Bracing: 0.15×0.15m

Create all sections in parallel in one call batch.

### 5. Create Elements

Use `create_beam_elements` with all elements in one list. **Build the list locally first, then send in one call** (MCP tool accepts unlimited list).

Element ID numbering convention:
- Group by type: girders first, then arch ribs, cross beams, hangers, struts, bracing
- Material assignment: girders/cross beams/bracing → A36; arch ribs/hangers → A572-50

### Critical: Zero-Length Element Check

Before sending elements, verify no element connects nodes with identical coordinates. Common trap:
- **Arch end hangers**: arch and girder meet at Z=0 at X=0 and X=L → skip end hangers
- Format: for `[Ni, Nj]`, check that `node[Ni].xyz != node[Nj].xyz`

### 6. Create Supports

Use `create_supports_custom` with 7-char constraint strings:
- `"1110000"` = fixed hinge (Dx+Dy+Dz constrained)
- `"0110000"` = Y-direction sliding
- `"1010000"` = X-direction sliding
- `"0010000"` = Z-only (vertical support)

Common bridge support pattern:
- One fixed corner → `1110000`
- One longitudinally free → `0110000`
- Transverse free on far side → `1010000`
- Expansion free → `0010000`

Apply one support at a time (different constraint per node).

### 7. Beam End Releases

**This is critical for structural accuracy.** Without releases, all connections are rigid, producing fake moments.

Use `create_beam_end_release`:
- **Hangers**: `release_i=["Mz"], release_j=["Mz"]` — pin-connected tension rods
- **Bracing (X-bracing, lateral)**: `release_i=["My","Mz"], release_j=["My","Mz"]` — truss members
- **Cross beams**: `release_i=["My","Mz"], release_j=["My","Mz"]` — shear-only connections to girders
- If `release_j` is omitted, it defaults to same as `release_i`

Available DOFs: Fx, Fy, Fz, Mx, My, Mz

### 8. Create Load Cases and Apply Loads

First create load cases with `create_load_case`:
- Use descriptive names: "恒载-DL", "活载-LL", "风载-WL"
- case_type: "D"=dead, "L"=live, "W"=wind, "USER"=custom

Then apply loads. **Important: the ID auto-increment bug is fixed**, but be aware:

For `apply_beam_udl`:
- `direction`: "GZ" = global Z down; "LZ" = local Z
- `value`: negative = downward (GZ). In tonf/m.
- Apply loads to ALL elements of a type in one call (not element-by-element)

For multiple load cases on the same elements: each call automatically gets a unique ITEMS ID now.

### 9. Run Analysis

`run_static_analysis` — simple, no parameters needed.

### 10. Extract Results

- `get_nodal_displacements(load_case_name)` — all node displacements
- `get_reactions(load_case_name)` — support reactions
- `get_beam_forces(load_case_name)` — element internal forces

Results use model units: forces in tonf, displacements in meters.

Always verify load balance: total applied load ≈ sum of reactions.

## Common Errors and Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| "边界条件没有定义" | Old code used `/db/CONS` (uppercase) instead of `/db/cons` | Fixed in domain layer. Restart MCP server if still happening |
| Analysis runs but results are all zeros | Load ID overwrite — same ID for multiple load cases on same elements | Fixed: domain now auto-increments IDs. Or use Bash to PUT both loads in one call |
| "几何形状不正确" on element N | Zero-length element (both ends at same coordinates) | Remove the element — check arch-girder intersection at X=0 and X=L |
| Material creation 400 error | Material not found in database | Fallback to `create_user_steel_material` with manual E, ν, density |
| Reaction doesn't match total load | Wrong unit interpretation or loads lost between sessions | Re-apply loads and re-run analysis. Verify: total FZ = Σ(load × length × count) |

## Worked Example: 50m Double-Arch Steel Bridge

See the full conversation transcript for a complete step-by-step example:
- 44 nodes: 2 girders + 2 arch ribs, 11 positions each
- 102 elements: girders(20) + arches(20) + cross beams(11) + hangers(18) + struts(5) + trans bracing(8) + long bracing(20)
- 2 materials: A36 + A572-50
- 6 sections: MainGirder, CrossBeam, ArchRib, Hanger, Strut, Bracing
- 4 abutment supports with different constraints
- 18 hanger Mz releases + 32 bracing My+Mz releases + 11 cross beam My+Mz releases
- 2 load cases: DL (-90 tonf/m) + LL (-6 tonf/m) on 20 girder elements
- Midspan deflection: ~554 mm under DL, ~37 mm under LL
