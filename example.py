import random
import streamlit as st
import streamlit_qs as stqs


"""
# Streamlit QueryString

This app shows off the [Query String Utility Functions](https://github.com/Asaurus1/streamlit-qs) for
Streamlit.

If you want to try this at home, you'll first need to install it:

```python
pip install git+https://github.com/Asaurus1/streamlit-qs.git@main
```

The functions in this library allow you to easily create "permalink-like" functionality in your application,
This can let users to share links with others that will populate streamlit with the same set of input values
that they were using. Or you can use the query string to pass data into your streamlit application from
another website or program.

## The Basics

### Getting Input

`text_input_qs` is a text input box that can read its initial/default value from the query string.

The only major difference between these qs elements and the standard streamlit elements is that
the qs elements *require* a `key` as a keyword argument.

"""
with st.echo():
    st.markdown(
        "Click this URL: "
        "[?input_some_text=Hello+World](?input_some_text=Hello+World)"
    ) 
    stqs.text_input_qs("Enter Some Text", key="input_some_text")
    
if stqs.from_query_args("input_some_text") == "Hello World":
    st.success("Nice Job! Notice what happened in your browser's URL bar ☝️☝️☝️")

""

"""
### Multi-select

Multi-select boxes can be filled using multiple key-value pairs with the same key.
"""
st.markdown("[Click this URL](?multi=Streamlit&multi=QS&multi=Rocks#multi-select)") 
with st.echo():
    values = stqs.multiselect_qs(
        label="Your opinion about this library:", 
        options=["Streamlit", "QS", "Rocks", "I", "Don't", "Know"],
        default=["I", "Don't", "Know"],
        key="multi",
    )
    
    if values == ["Streamlit", "QS", "Rocks"]:
        st.success("That's Right!")
        
"""
For additional examples of all the qs elements you can use, see [Element Examples](#element-examples) below.
"""

"""
## Modifying the Query String

### Autoupdate

Qs elements can also auto-fill their new value into the query string when they are changed by the user. 
Turn this on using the `autoupdate` argument:
"""
with st.echo():
    stqs.selectbox_qs(
        "Select an option:", 
        options=["A", "B", "C"], 
        key="auto_select1", 
        autoupdate=True
    )
    stqs.selectbox_qs(
        "Select another option:", 
        options=["A", "B", "C"], 
        key="auto_select2", 
        autoupdate=True
    )

""
"""
#### Callbacks

Autoupdate works by adding some function calls to the `on_change` callback, but it seamlessly wraps your own
callbacks as well so that they're still usable. 
This example updates the query string AND creates balloons or snow!
"""
with st.echo():
    stqs.selectbox_qs(
        "Select an option:", 
        options=["I love winter", "I like parties"], 
        key="auto_select3", 
        autoupdate=True, 
        on_change=random.choice([st.balloons, st.snow]),
    )

""

"""
### Permalinks

Create your own permalinks using markdown or HTML with the `make_query_string` function.
By default the permalink generates a query string pair for every user element on the page,
even those that aren't qs elements.
"""
with st.echo():
    permalink = stqs.make_query_string()
    st.markdown(f"[permalink everything]({permalink})")

""

"""
You can limit the query strings using a hard-coded list of `key`s or a regular expression
to match specific `key` values.
"""
with st.echo():
    somekeys_link = stqs.make_query_string(keys=['multi'])
    st.markdown(f"[only some keys]({somekeys_link})")
    
    regex_link = stqs.make_query_string(regex=['auto.*'])
    st.markdown(f"[regular expressions :D]({regex_link})")
""
""

"""
## Element Examples

coming soon...

"""
# stqs.selectbox_qs("Options", ["option1", "option2"], key="option", autoupdate=True)
# stqs.selectbox_qs("Number", ["1", "2", "3"], key="number", autoupdate=True)
# stqs.text_input_qs("My Name", key="name", autoupdate=True)
# stqs.radio_qs("Number 2", ["1", "2", "3"], key="number2", autoupdate=True)
# stqs.checkbox_qs("Yes", True, key="yes", autoupdate=True)
# stqs.multiselect_qs("letter", ["a", "b", "c"], key="letter", default=["c", "a"])
# stqs.multiselect_qs(
#     "Format Funcs",
#     ["x", "y", "z"],
#     key="hellonumber",
#     format_func=lambda x: f"Pick: {x}",
#     autoupdate=True,
# )
# stqs.number_input_qs("Number 3", key="number3", autoupdate=True)
# stqs.text_area_qs("Text Area", placeholder="This is a big text area", key="textarea")

# # Some UI buttons
# st.markdown(f"[permalink]({stqs.make_query_string()}) (right click to copy)")
# st.button("Update URL with parameters", on_click=stqs.update_qs_callback())
# st.button("Clear URL", on_click=stqs.clear_qs_callback())