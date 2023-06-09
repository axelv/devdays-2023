# Let's build FHIR clients in Python

You can find all the examples in the `notebooks/` folder.
They are organised in folders with some supporting Python modules.

## Setting up your environment.

You have three options to setup the environment for this project.

1. Github Codespaces
   
   - On the GitHub repository page, click on the green 'Code' button then 'CodeSpaces' > 'Create codespace on master'.
   - Once the environment has booted succesfully. Run `pip install -r requirements.txt` to install dependencies.


2. VSCode (using devcontainer)

    - On the GitHub repository page, click on the green 'Code' button then 'CodeSpaces' > 'Create codespace on master'
    - Once the environment has booted succesfully. Run `pip install -r requirements.txt` to install dependencies.


3. VSCode (setup the environment yourself)

    - Make sure you have Python 3.11 and Poetry installed
    - Export a `requirements.txt` from using `poetry export --without-hashes > requirements.txt`
    - `pip install -r requirements.txt` to install dependencies.