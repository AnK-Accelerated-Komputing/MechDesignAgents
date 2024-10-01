# %%

# The markers "# %%" separate code blocks for execution (cells) 
# Press shift-enter to exectute a cell and move to next cell
# Press ctrl-enter to exectute a cell and keep cursor at the position
# For more details, see https://marketplace.visualstudio.com/items?itemName=ms-toolsai.jupyter

# %%

import cadquery as cq
from ocp_vscode import *

# %%

b = cq.Workplane().box(1,2,3).fillet(0.1)

show(b)
