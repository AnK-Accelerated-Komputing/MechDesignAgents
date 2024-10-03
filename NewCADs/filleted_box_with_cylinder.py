# filename: filleted_box_with_cylinder.py
import cadquery as cq
from ocp_vscode import *

# Step 1: Define Parameters
length = 500.0
width = 100.0
height = 30.0
fillet_radius = 5.0
cylinder_radius = 50.0
cylinder_height = 100.0

# Step 2: Create the CAD Model
box = (
    cq.Workplane("XY")
    .box(length, width, height)
    .edges("|Z or >Z").fillet(fillet_radius)
)

cylinder = (
    cq.Workplane("XY")
    .moveTo(-cylinder_radius, -cylinder_radius)  # Move to the center of the box
    .circle(cylinder_radius)
    .extrude(cylinder_height)
    .translate((length/2 - cylinder_radius, width/2 - cylinder_radius, height/2))  # Translate to the center of the box
)

model = box.union(cylinder)  # Combine the box and cylinder

# Step 3: Save the Model
cq.exporters.export(model, "filleted_box_with_cylinder.stl")
cq.exporters.export(model.section(), "filleted_box_with_cylinder.dxf")
cq.exporters.export(model, "filleted_box_with_cylinder.step")

# Step 4: Visualize the Model
show(model)