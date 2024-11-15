import base64
from groq import Groq
import os
from rich.console import Console
from rich.markdown import Markdown

# Read and encode the image
with open("/home/niel77/MechanicalAgents/mechdesignagents/images/Drawing-of-the-connecting-rod_W640.jpg", "rb") as image_file:
    encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
    image_data_url = f"data:image/png;base64,{encoded_image}"

client = Groq(api_key=os.environ["GROQ_API_KEY"])

completion = client.chat.completions.create(
    model="llava-v1.5-7b-4096-preview",
    # model="llama-3.2-90b-vision-preview",


    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "You translate image provided by user into detailed drawing specifications.  Provide dimensions, tolerances, materials, and other necessary information for creating a professional engineering drawing.  Always respond in a structured format, separating different aspects of the drawing clearly."
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_data_url
                    }
                }
            ]
        }
    ],
    temperature=0,
    max_tokens=1024,
)

# Get the response content
markdown_content = completion.choices[0].message.content

# Create a Markdown object
md = Markdown(markdown_content)
console = Console()
# Print formatted markdown
console.print(md)