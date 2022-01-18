# Developing RVC2MQTT

- Use python 3.9 or newer

## Setup

1. create a python virtual environment
    I prefer to do this in the one directory above (outside) my git repository.
    This works well for vscode
    ``` bash
    python3 -m venv venv
    ```

2. activate your virtual environment
    * On Windows
        ``` bash
        <name of virtual environment>/Scripts/activate.bat
        ```
    * On Linux
        ``` bash
        source <name of virtual environment>/bin/activate
        ```
3. install dependencies
    ``` bash
    pip install -r requirement.txt
    ```

4. install optional/development requirements
    ``` bash
    pip install -r requirement.dev.txt
    ```

## Unit-Testing

``` bash
pytest -v --html=pytest_report.html --self-contained-html --cov=rvc2mqtt --cov-report html:cov_html
```
Check out the results in `pytest_report.html`
Check out the code coverage in `cov_html/index.html`

