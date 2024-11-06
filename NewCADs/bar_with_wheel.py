# filename: bar_with_wheel.py
import cadquery as cq
from ocp_vscode import *

# Step 1: Define Parameters
bar_length = 100.0
bar_width = 10.0
bar_height = 20.0
wheel_diameter = 20.0
wheel_thickness = 5.0

# Step 2: Create the CAD Model
bar = cq.Workplane("XY").box(bar_length, bar_width, bar_height)
wheel = cq.Workplane("XY").circle(wheel_diameter / 2).extrude(wheel_thickness)
wheel = wheel.translate((bar_length - wheel_thickness, 0, bar_height / 2 - wheel_diameter / 2))  # move the wheel to the end of the bar
model = bar.union(wheel)

# Step 3: Save the Model
cq.exporters.export(model, "bar_with_wheel.stl")
cq.exporters.export(model.section(), "bar_with_wheel.dxf")
cq.exporters.export(model, "bar_with_wheel.step")

# Step 4: Visualize the Model
show(model)