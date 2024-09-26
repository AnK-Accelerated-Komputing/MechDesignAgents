# filename: plate_with_hole.py
import cadquery as cq

# Create a new workplane
workplane = cq.Workplane("XY")

# Create a plate
plate = workplane.box(20, 20, 2)

# Create a hole
hole = workplane.circle(5).extrude(-2)

# Cut the hole from the plate
plate = plate.cut(hole)

# Display the plate
cq.Workplane.show_object(plate)