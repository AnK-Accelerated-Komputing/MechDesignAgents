# filename: filleted_box_with_cylinder_and_sphere.py
import cadquery as cq
from ocp_vscode import *

# Step 1: Define Parameters
length = 500.0
width = 100.0
height = 30.0
fillet_radius = 5.0
cylinder_radius = 50.0
cylinder_height = 100.0
sphere_radius = 20.0

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

sphere = (
    cq.Workplane("XY")
    .moveTo(length/2, -width/2)  # Move to the edge of the box
    .sphere(sphere_radius)
    .translate((0, 0, height/2))  # Translate to the edge of the box in the Z direction
)

model = box.union(cylinder).union(sphere)  # Combine the box, cylinder, and sphere

# Step 3: Save the Model
cq.exporters.export(model, "filleted_box_with_cylinder_and_sphere.stl")
cq.exporters.export(model.section(), "filleted_box_with_cylinder_and_sphere.dxf")
cq.exporters.export(model, "filleted_box_with_cylinder_and_sphere.step")

# Step 4: Visualize the Model
show(model)