# MechDesignAgents

## Overview
[Provide a brief overview of your project here.]


## Deployment

### Linux
#### Open the terminal in required directory
```bash
cd "path"
```

#### Clone the repository
To deploy this project, first clone this repository:

```bash
git clone https://github.com/AnK-Accelerated-Komputing/MechDesignAgents.git
```

#### Navigate into the cloned directory:
``` bash
cd MechDesignAgents
```
#### Create a virtual Environment 
If you are same folder: 
``` bash
python3 -m venv /path/to/new_venv
```

#### Source the v-env (Virtual Environment):
``` bash
source venv/bin/activate 
source /media/........./MechDesignAgents/.venv/bin/activate
```

#### Requirements
Now, install the necessary packages and
``` bash
pip install -r requirements.txt
```

Make sure you have Python 3.6 or higher installed.


### Windows

#### Open the terminal in required directory
```bash
cd "path"
```

#### Clone the repository
To deploy this project, first clone this repository:

```bash
git clone https://github.com/AnK-Accelerated-Komputing/MechDesignAgents.git
```

#### Navigate into the cloned directory:
``` bash
cd MechDesignAgents
```
#### Create a virtual Environment 
If you are same folder: 
``` bash
python3 -m venv /path/to/new_venv
```

#### Source the v-env (Virtual Environment):
``` bash
venv\Scripts\activate 
 path_to_your_venv\Scripts\activate
```

#### Requirements
Now, install the necessary packages and
``` bash
pip install -r requirements.txt
```


Make sure you have Python 3.6 or higher installed.

#### Export GROQ API KEY in terminal
```bash 
export GROQ_API_KEY=<YOUR_API_KEY>
```


# MechDesignAgents File Summary

| File Name                     | Likely Purpose                                                                 |
|---------------------------------|---------------------------------------------------------------------------------|
| `__init__.py`                  | Initializes the `mechdesignagents` Python package by importing all necessary components from agent and design files.                             |
| `agents.py`                    | Defines multiple agents for user interaction. EachEach agent has specific configurations and roles in the chat system.|
| • Designer Agent | A user proxy that interacts with humans to gather design requirements.|
| • Retrieve User Proxy Agent | An agent that assists in retrieving content relevant to design problems.  | 
| • CadQuery Code Writer | Generates Python code to create CAD models using CadQuery. |
| • Code Reviewer | Reviews the generated code for adherence to specified formats and guidelines.  |  
| `designer_cadcoder.py`         | Simple implementation where the designer agent initiates a chat with the CadQuery code writer based on a design problem input by the user. |
| `designers_no_rag.py`          | Implements a group chat system without RAG (Retrieval-Augmented Generation), where all agents can interact to resolve a design problem collaboratively.     |
| `designers_rag.py`             | Similar to designers_no_rag.py, but integrates a retrieval component, allowing the CadQuery code writer to retrieve relevant content before generating code.      |
| `mechagents_old_streamlit.py` | This appears to be a user interface built using Streamlit, allowing users to select models and input API keys for interaction with the agents. It initializes the agents and manages user input. |




## FAQ

#### How to check the install packages? 
``` bash 
pip list
```

#### How to verify the installion? 

```bash
pip show <package_name>
```

#### If error occur during Installation? 
Make sure your pip and setuptools are up to date by executing command: :
```bash
pip install --upgrade pip setuptools

```

####  Dependency conflict between the installed version of package? 
For eg: nstalling collected packages: numpy
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed. This behaviour is the source of the following dependency conflicts.
nlopt 2.8.0 requires numpy<3,>=2, but you have numpy 1.26.4 which is incompatible.
```bash
pip uninstall -y numpy && pip install numpy==1.24.0

pip uninstall -y <conflict_package_name> && pip install <conflict_package_name>==<replace_your_required_version>

```