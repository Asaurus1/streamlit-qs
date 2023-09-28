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
pip install streamlit-qs
```

The functions in this library allow you to easily create "permalink-like" functionality in your application,
This can let users to share links with others that will populate streamlit with the same set of input values
that they were using. Or you can use the query string to pass data into your streamlit application from
another website or program. The only thing that's realy different about the streamlit_qs widgets is that
you *must* always give them a unique `key=` argument, which is used to encode and decode the value of the
widget in the browser URL.

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
st.markdown("Click this URL: [?multi=Streamlit&multi=QS&multi=Rocks](?multi=Streamlit&multi=QS&multi=Rocks#multi-select)")
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

"""With Streamlit 1.27.0+, you can even use a value of "None" as a default value or index.
When this is the case, clearing the textbox *removes* the `auto_select2` parameter from the URL.
"""
with st.echo():
    stqs.selectbox_qs("Select another option:",
        options=["A", "B", "C"],
        index=None,
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

"""You can also use the `update_qs_callback`, `add_qs_callback`, and `clear_qs_callback` functions to allow buttons and other streamlit
widgets to manage the query string. For example, you can make a button that adds a specific widget's value to the URL;
"""
with st.echo():
    st.button("Add 'multi' to URL", on_click=stqs.add_qs_callback(["multi"]))

"""
### Permalinks

Create your own permalinks using markdown or HTML with the `make_query_string` function.
By default the permalink generates a query string pair for every user element on the page,
even those that aren't qs elements.
"""
with st.echo():
    permalink = stqs.make_query_string() + "#permalinks"
    st.markdown(f"[permalink everything]({permalink})")
    st.code(permalink, language="markdown")

""

"""
You can limit the query strings using a hard-coded list of `key`s or a regular expression
to match specific `key` values.
"""
with st.echo():
    somekeys_link = stqs.make_query_string(keys=['multi'])
    st.markdown(f"[only some keys 💃]({somekeys_link})")
    st.code(somekeys_link, language="markdown")
    
    regex_link = stqs.make_query_string(regex=['auto.*'])
    st.markdown(f"[regular expressions 🤔]({regex_link})")
    st.code(regex_link, language="markdown")

""
""


def show_docstring(func):
    st.markdown(f"#### `{func.__name__}`")
    with st.expander("Docstring"):
        st.help(func)


"""
## Element Examples

In this section, you will find individual examples of all the streamlit_qs widgets and functions.

"""
show_docstring(stqs.text_input_qs)
st.write("Example:")
with st.echo():
    stqs.text_input_qs("My Name", default="", key="name", autoupdate=True)
st.divider()

show_docstring(stqs.text_area_qs)
st.write("Example:")
with st.echo():
    stqs.text_area_qs("Text Area",
        placeholder="This is a big text area that DOESN'T autoupdate",
        key="textarea",
        default=None,
    )
    st.button("But you can update the query string manually",
        on_click=stqs.add_qs_callback(["textarea"])
    )
st.divider()

show_docstring(stqs.selectbox_qs)
st.write("Example:")
with st.echo():
    stqs.selectbox_qs("Options", ["option1", "option2"], key="option", autoupdate=True)
    stqs.selectbox_qs("Number", [1, 2, 3], index=None, key="number", autoupdate=True)
st.divider()

show_docstring(stqs.radio_qs)
st.write("Example:")
with st.echo():
    stqs.radio_qs("Number 2", ["1", "2", "3"], index=None, key="number2", autoupdate=True)
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

with st.expander("More Info: Format Funcs"):
    st.info("""
The `format_func` argument does not affect the values in the query string. There is not currently a way
to specify a serialization function for custom object types; you are encouraged to convert them to strings
yourself ahead of passing them to the streamlit_qs widget. If this is a feature you'd like to see added,
feel free to leave a feature request issue on the Github. """)
    st.write("Example:")
    with st.echo():
        stqs.multiselect_qs("Format Funcs",
            ["x", "y", "z"],
            key="hellonumber",
            format_func=lambda x: f"Pick: {x}",
            autoupdate=True,
        )
with st.expander("More Info: Unformat Funcs"):
    st.info(
        "You can use non-string objects as well; the streamlit_qs functions "
        "will detect ints, floats, and members of an Enum and convert them automatically, "
        "or you can use the `unformat_func` argument to provide a custom str->option converter. "
        "Here we are using the `unenumifier` function that comes with streamlit_qs to explicitly "
        "convert back to `AnEnum` type."
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
            # the unformat_func argument will be automatically
            # inferred for you when using an Enum, so feel free to
            # leave it out.
        )
st.divider()

show_docstring(stqs.number_input_qs)
st.write("Example:")
with st.echo():
    stqs.number_input_qs("Number 3", default=None, key="number3", autoupdate=True)
st.divider()


"""
### Query string utils

"""
show_docstring(stqs.make_query_string)
st.write("Example:")
with st.echo():
    st.markdown(f"[permalink]({stqs.make_query_string()}) (right click to copy)")
st.divider()

show_docstring(stqs.set_qs_callback)
st.write("Example:")
with st.echo():
    st.button("Update URL with parameters", on_click=stqs.set_qs_callback())
st.divider()

show_docstring(stqs.clear_qs_callback)
st.write("Example:")
with st.echo():
    st.button("Clear URL", on_click=stqs.clear_qs_callback())

""
with st.expander("More Info: Resetting a widget..."):
    st.info("""Note: Clearing the query string does not automatically clear any widgets. If you want to
    also reset a widget's value to what is in the URL, you should delete it's value from `st.session_state`
    instead. Check out this example below.""")

    with st.echo():
        placeholder = st.empty()

        if st.button("#1. Click to Pre-fill the widget and URL"):
            # Update the widget value and then call a callback function to update the URL.
            st.session_state.clearabletext = "clearme"
            stqs.set_qs_callback(["clearabletext"])()

        st.write("#2. Then change the text in this widget to something else")

        if st.button("#3. Reset this Widget"):
            del st.session_state.clearabletext

        with placeholder:
            stqs.text_input_qs("Clearable text field", key="clearabletext")

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
        on_click=stqs.set_qs_callback(["stay_invisible", "show_in_query_string"])
    )

    # Query String does NOT contain "stay_invisible" after the button is clicked.