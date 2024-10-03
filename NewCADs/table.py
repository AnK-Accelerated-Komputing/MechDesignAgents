# filename: table.py
import cadquery as cq
from ocp_vscode import *

# Step 1: Define Parameters
table_top_length = 2000.0
table_top_width = 1000.0
table_top_thickness = 10.0

leg_length = 50.0
leg_width = 50.0
leg_height = 1000.0

fillet_radius = 10.0

# Step 2: Create the CAD Model
table_top_wp = cq.Workplane("XY").box(table_top_length, table_top_width, table_top_thickness)
table_top = table_top_wp.val().edges("|Z").fillet(fillet_radius, table_top_wp.val().edges("|Z"))  # Corrected line

leg1_wp = cq.Workplane("XY").box(leg_length, leg_width, leg_height)
leg1 = leg1_wp.val().edges("|Z").fillet(fillet_radius, leg1_wp.val().edges("|Z"))  # Corrected line
leg2 = leg1_wp.val().translate((table_top_length - leg_length, 0, 0)).edges("|Z").fillet(fillet_radius, leg1_wp.val().translate((table_top_length - leg_length, 0, 0)).edges("|Z"))  # Corrected line
leg3 = leg1_wp.val().translate((table_top_length - leg_length, table_top_width - leg_width, 0)).edges("|Z").fillet(fillet_radius, leg1_wp.val().translate((table_top_length - leg_length, table_top_width - leg_width, 0)).edges("|Z"))  # Corrected line
leg4 = leg1_wp.val().translate((0, table_top_width - leg_width, 0)).edges("|Z").fillet(fillet_radius, leg1_wp.val().translate((0, table_top_width - leg_width, 0)).edges("|Z"))  # Corrected line

table_assembly = cq.Assembly()
table_assembly.add(table_top, name="table_top", loc=cq.Location(cq.Vector(0, 0, table_top_thickness)))
table_assembly.add(leg1, name="leg1", loc=cq.Location(cq.Vector(0, 0, -leg_height)))
table_assembly.add(leg2, name="leg2", loc=cq.Location(cq.Vector(0, 0, -leg_height)))
table_assembly.add(leg3, name="leg3", loc=cq.Location(cq.Vector(0, 0, -leg_height)))
table_assembly.add(leg4, name="leg4", loc=cq.Location(cq.Vector(0, 0, -leg_height)))

# Step 3: Save the Model
cq.exporters.export(table_assembly, "table.stl")
cq.exporters.export(table_assembly.val(), "table.dxf")
cq.exporters.export(table_assembly, "table.step")

# Step 4: Visualize the Model
show(table_assembly)