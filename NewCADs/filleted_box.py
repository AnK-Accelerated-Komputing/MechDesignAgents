# filename: filleted_box.py
import cadquery as cq
from ocp_vscode import *

# Step 1: Define Parameters
length = 500.0
width = 100.0
height = 30.0
fillet_radius = 5.0

# Step 2: Create the CAD Model
box = (
    cq.Workplane("XY")
    .box(length, width, height)
    .edges("|Z or >Z").fillet(fillet_radius)
)

# Step 3: Save the Model
cq.exporters.export(box, "filleted_box.stl")
cq.exporters.export(box.section(), "filleted_box.dxf")
cq.exporters.export(box, "filleted_box.step")

# Step 4: Visualize the Model
show(box)