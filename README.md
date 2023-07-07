# Query String functions for Streamlit
This app shows off the [Query String Utility Functions](https://github.com/Asaurus1/streamlit-qs) for Streamlit.

The functions in this library allow you to easily create "permalink-like" functionality in your application,
This can let users to share links with others that will populate streamlit with the same set of input values
that they were using. Or you can use the query string to pass data into your streamlit application from
another website or program.

> ### A note about the experimental API:
>
> Query string interaction within Streamlit is currently experimental, and the API is subject to change at any time
> This library works with v1.23.1 of Streamlit but may not be forward compatible with future versions when the 
> experimental query string API is either A) removed, B) made standard, or C) modified in some incompatible way.
>
> Please submit an issue if you encounter compatibility issues with future versions of Streamlit.


## Installation

First install Streamlit (of course!) then install this library:

```bash
pip install streamlit-qs
```
or
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
