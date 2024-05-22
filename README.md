# QueryParams Widgets for Streamlit

[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/asaurus1/streamlit-qs/pdm.yml)](https://github.com/Asaurus1/streamlit-qs/actions)
[![GitHub last commit](https://img.shields.io/github/last-commit/asaurus1/streamlit-qs)](https://github.com/Asaurus1/streamlit-qs)
[![PyPI - Version](https://img.shields.io/pypi/v/streamlit-qs)](https://pypi.org/project/streamlit-qs/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/streamlit-qs)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/streamlit-qs)
![PyPI - Implementation](https://img.shields.io/pypi/implementation/streamlit-qs)
![PyPI - Downloads](https://img.shields.io/pypi/dm/streamlit-qs)
[![Licence](https://img.shields.io/badge/licence-Apache%202.0-blue)](https://www.apache.org/licenses/LICENSE-2.0)
[![Streamlit Version](https://img.shields.io/badge/Streamlit->=1.30.0-blue)](https://github.com/streamlit/streamlit)
[![pdm-managed](https://img.shields.io/badge/pdm-managed-blueviolet)](https://pdm-project.org)

The functions in this library allow you to easily create "permalink-like" functionality in your application,
This can let users to share links with others that will populate streamlit with the same set of input values
that they were using. Or you can use the query string to pass data into your streamlit application from
another website or program.


## Installation

First install Streamlit (of course!) then install this library:

```bash
pip install streamlit-qs
```
Or, to install the latest source:
```bash
pip install git+https://github.com/Asaurus1/streamlit-qs.git@main
```

## Example

```python
import streamlit as st
import streamlit_qs as stqs

st.markdown("[Click this URL](?input_some_text=Hello+World)") 
stqs.text_input_qs("Enter Some Text", key="input_some_text")
```

For more examples, including :sparkles:**customization options**:sparkles:, see
[the demo app](https://query-string.streamlit.app/).


## Version Compatibility
For Streamlit v1.29.0 or below use release v0.2.0 of this app
For Streamlit v1.30.0 or above, use the latest released version of this app above v0.2.0