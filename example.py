from enum import Enum
import random
import streamlit as st
import streamlit_qs as stqs

# st.set_page_config(layout="wide")

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

"""
with st.expander("A note about the experimental API"):
    st.info(
        "Query string interaction within Streamlit is currently experimental, "
        "and the API is subject to change at any time. This library works with "
        "v1.23.1 of Streamlit but may not be forward compatible with future versions "
        "when the experimental query string API is either A) removed, B) made standard, "
        "or C) modified in some incompatible way\n\n"
        "Please submit an issue if you encounter compatibility issues with future "
        "versions of Streamlit."
    )
    
"""

## The Basics

### Getting Input

`text_input_qs` is a text input box that can read its initial/default value from the query string.

The only major difference between these qs elements and the standard streamlit elements is that
the qs elements *require* a `key` as a keyword argument.

"""
with st.echo():
    st.markdown(
        "Click this URL: "
        "[?input_some_text=Hello+World](?input_some_text=Hello+World#the-basics)"
    ) 
    text = stqs.text_input_qs("Enter Some Text", key="input_some_text")
    
if text == "Hello World":
    st.success("Nice Job! Notice what happened in your browser's URL bar ☝️☝️☝️")

""

"""
### Multi-select

Multi-select boxes can be filled using multiple key-value pairs with the same key.
"""
st.markdown("[Click this URL](?multi=Streamlit&multi=QS&multi=Rocks#multi-select)") 
with st.echo():
    values = stqs.multiselect_qs("Your opinion about this library:",
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
    stqs.selectbox_qs("Select an option:",
        options=["A", "B", "C"], 
        key="auto_select1", 
        autoupdate=True
    )
    stqs.selectbox_qs("Select another option:",
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
    stqs.selectbox_qs("Select an option:",
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


def show_docstring(func):
    st.markdown(f"#### `{func.__name__}`")
    with st.expander("Docstring"):
        st.help(func)


"""
## Element Examples

"""
show_docstring(stqs.text_input_qs)
st.write("Example:")
with st.echo():
    stqs.text_input_qs("My Name", key="name", autoupdate=True)
st.divider()

show_docstring(stqs.text_area_qs)
st.write("Example:")
with st.echo():
    stqs.text_area_qs("Text Area",
        placeholder="This is a big text area that DOESN'T autoupdate",
        key="textarea"
    )
    st.button("But you can update the query string manually",
        on_click=stqs.add_qs_callback(["textarea"])
    )
st.divider()

show_docstring(stqs.selectbox_qs)
st.write("Example:")
with st.echo():
    stqs.selectbox_qs("Options", ["option1", "option2"], key="option", autoupdate=True)
    stqs.selectbox_qs("Number", [1, 2, 3], key="number", autoupdate=True)
st.divider()

show_docstring(stqs.radio_qs)
st.write("Example:")
with st.echo():
    stqs.radio_qs("Number 2", ["1", "2", "3"], key="number2", autoupdate=True)
st.divider()

show_docstring(stqs.checkbox_qs)
st.write("Example:")
with st.echo():
    stqs.checkbox_qs("Yes", True, key="yes", autoupdate=True)
st.divider()

show_docstring(stqs.multiselect_qs)
st.write("Example:")
with st.echo():
    stqs.multiselect_qs("letter", ["a", "b", "c"], key="letter", default=["c", "a"], autoupdate=True)
st.write("")
st.info("Note: format_func does not affect the values in the query string")
st.write("Example:")
with st.echo():
    stqs.multiselect_qs("Format Funcs",
        ["x", "y", "z"],
        key="hellonumber",
        format_func=lambda x: f"Pick: {x}",
        autoupdate=True,
    )
st.write("")
st.info(
    "Note: You can use non-string objects as well, and the `unenumifier` function "
    "helps to convert query string values back into Enums"
)
st.write("Example:")
with st.echo():
    class AnEnum(Enum):
        FOO = 0
        BAR = 1

    stqs.multiselect_qs("Enums",
        options=[AnEnum.FOO, AnEnum.BAR],
        key="enum",
        autoupdate=True,
        unformat_func = stqs.unenumifier(AnEnum)
    )
st.divider()

show_docstring(stqs.number_input_qs)
st.write("Example:")
with st.echo():
    stqs.number_input_qs("Number 3", key="number3", autoupdate=True)
st.divider()


"""
### Query string utils

"""
show_docstring(stqs.make_query_string)
st.write("Example:")
with st.echo():
    st.markdown(f"[permalink]({stqs.make_query_string()}) (right click to copy)")
st.divider()

show_docstring(stqs.update_qs_callback)
st.write("Example:")
with st.echo():
    st.button("Update URL with parameters", on_click=stqs.update_qs_callback())
st.divider()

show_docstring(stqs.clear_qs_callback)
st.write("Example:")
with st.echo():
    st.button("Clear URL", on_click=stqs.clear_qs_callback())
st.divider()

show_docstring(stqs.blacklist_key)
show_docstring(stqs.unblacklist_key)
st.write("Example:")
with st.echo():
    stqs.blacklist_key("stay_invisible")
    st.session_state.stay_invisible = 0
    st.session_state.show_in_query_string = 1

    st.button(
        "Update Query String",
        on_click=stqs.update_qs_callback(["stay_invisible", "show_in_query_string"])
    )

    # Query String does NOT contain "stay_invisible"
    # after calling update_qs