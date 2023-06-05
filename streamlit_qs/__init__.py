"""Query string extensions for Streamlit"""
from __future__ import annotations

import functools
import re
import urllib.parse
from typing import (
    Any,
    Callable,
    Collection,
    KeysView,
    List,
    Mapping,
    MutableMapping,
    Sequence,
    TypeVar,
    cast,
    overload,
)

import streamlit as st
from streamlit.elements.number_input import NoValue, Number
from typing_extensions import Literal


T = TypeVar("T")


# A list of query string keys are are not allowed because they are used
# elsewhere in application backend code. Expected to be set by the user at
# application initalization
QS_BLACKLIST_KEYS: List[str] = []


def selectbox_qs(label: str, options: Sequence[str], index: int = 0, *, key: str, autoupdate: bool = False, **kwargs) -> str | None:
    """Create a streamlit selectbox which automatically populates itself from the URL query string.

    Takes all arguments that st.selectbox takes, but the "key" keyword argument _must_ be provided. Returns the value
    selected by the user.

    Note: For the moment this only works with options that are lists of strings. Converting the results to non-strings,
    such as ints or floats, is left to the caller.
    """
    if autoupdate:
        _wrap_on_change_with_qs_update(key, kwargs)
    return st.selectbox(label, options, index=from_query_args_index(key, options, default=index), key=key, **kwargs)


def radio_qs(label: str, options: Sequence[str], index:int = 0, *, key: str, autoupdate: bool = False, **kwargs) -> str | None:
    """Create a streamlit radio widget which automatically populates itself from the URL query string.

    Takes all arguments that st.radio takes, but the "key" keyword argument _must_ be provided. Returns the value
    selected by the user. "autoupdate" causes that value to also be populated into the URL query string on change.

    Note: For the moment this only works with options that are lists of strings. Converting the results to non-strings,
    such as ints or floats, is left to the caller.
    """
    if autoupdate:
        _wrap_on_change_with_qs_update(key, kwargs)
    return st.radio(label, options, index=from_query_args_index(key, options, default=index), key=key, **kwargs)


_DEFAULT_SENTINEL_STR = "``hNqOh2eI3q47sM0EjxSSULji8oATCnhVbREJtPmxzzrSRIQgouOVvN38zzWs``"


def multiselect_qs(
    label: str,
    options: Sequence[T],
    default: Sequence[T] | T | None = None,
    *,
    key: str,
    discard_missing: bool = True,
    unformat_func: Any = str,
    autoupdate: bool = False,
    **kwargs,
) -> List[T]:
    """Create a streamlit multi_select widget which automatically populates itself from the URL query string.

    Takes all arguments that st.multiselect takes, but the "key" keyword argument _must_ be provided. Returns the value
    selected by the user. If the additional argument discard_missing is set to True, a ValueError will be raised
    if the query string contains selection options which are not in the set of available options.
    "autoupdate" causes that value to also be populated into the URL query string on change.
    "unformat_func" can be used to specify a callable that turns a string value from the query string back into a python
    object. For example, pass `unformat_func=int` to convert query string values to integers.
    """
    # if default is none, we need to pass an empty list to from_query_args, otherwise a sentinel string value
    # (since `default` itself is not necessarily a list of strings)
    maybe_from_query = from_query_args(key, default=[_DEFAULT_SENTINEL_STR], as_list=True)

    # Generate the "default" list of values to be passed to the underlying streamlit call.
    if maybe_from_query == [_DEFAULT_SENTINEL_STR]:
        ms_default_subset = default
        # Note: Any invalid default will get handled by the streamlit function, so we perform no filtering here.
    else:
        ms_default: List[T] = (
            cast(List[T], [val for val in maybe_from_query])
            if unformat_func is str 
            else [unformat_func(val) for val in maybe_from_query]
        )

        # Filter down to only the items that are present in the set of options
        ms_default_subset = [item for item in ms_default if item in options]

        # discard missing items or throw an exception if we got a value from the query string that is not in the options
        if not discard_missing and ms_default_subset != ms_default:
            raise ValueError(
                "Some query string options were not contained in the available options for multiselect "
                f'key = "{key}". Missing values: {[item for item in ms_default if item not in options]}'
            )

    if autoupdate:
        _wrap_on_change_with_qs_update(key, kwargs)
    return st.multiselect(label, options, default=ms_default_subset, key=key, **kwargs)


def checkbox_qs(label: str, default: bool = False, *, key: str, autoupdate: bool = False, **kwargs) -> bool:
    """Create a streamlit checkbox widget which automatically populates itself from the URL query string.

    Takes all arguments that st.radio takes, but the "key" keyword argument _must_ be provided.
    The following values will be treated as True: "true", "1" (case insensitive)
    The following values will be treated as False: "false", "0" (case insensitive)
    Any other value will result in the checkbox using the "default" value.

    "autoupdate" causes that value to also be populated into the URL query string on change.
    """
    query_arg = from_query_args(key, default="")
    if query_arg.lower() in ("1", "true"):
        query_bool = True
    elif query_arg.lower() in ("0", "false"):
        query_bool = False
    else:
        query_bool = default
    if autoupdate:
        _wrap_on_change_with_qs_update(key, kwargs)
    return st.checkbox(label, value=query_bool, key=key, **kwargs)


def text_input_qs(label: str, default: str = "", *, key: str, autoupdate: bool = False, **kwargs) -> str | None:
    """Create a streamlit text_input which automatically populates itself from the URL query string.

    Takes all arguments that st.text_input takes, but the "key" keyword argument _must_ be provided. Returns the value
    selected by the user. "autoupdate" causes that value to also be populated into the URL query string on change.
    """
    if autoupdate:
        _wrap_on_change_with_qs_update(key, kwargs)
    return st.text_input(label, value=from_query_args(key, default=default), key=key, **kwargs)


def text_area_qs(label: str, default: str = "", *, key: str, autoupdate: bool = False, **kwargs) -> str | None:
    """Create a streamlit text_area which automatically populates itself from the URL query string.

    Takes all arguments that st.text_area takes, but the "key" keyword argument _must_ be provided. Returns the value
    selected by the user. "autoupdate" causes that value to also be populated into the URL query string on change.
    """
    if autoupdate:
        _wrap_on_change_with_qs_update(key, kwargs)
    return st.text_area(label, value=from_query_args(key, default=default), key=key, **kwargs)


def number_input_qs(
    label: str, default: Number | NoValue | None = NoValue(), *, key: str, autoupdate: bool = False, **kwargs
) -> Number:
    """Create a streamlit number_input which automatically populates itself from the URL query string.

    Takes all arguments that st.number_input takes, but the "key" keyword argument _must_ be provided. Returns the value
    selected by the user. "autoupdate" causes that value to also be populated into the URL query string on change.
    """
    query_value: int | float | NoValue | None

    query_arg = from_query_args(key, default="NOT_A_NUMBER")
    if isinstance(default, (int, float)):
        expected_type = type(default)
    elif "min_value" in kwargs:
        expected_type = type(kwargs["min_value"])
    elif "max_value" in kwargs:
        expected_type = type(kwargs["max_value"])
    elif "step" in kwargs:
        expected_type = type(kwargs["step"])
    else:
        expected_type = float

    if not issubclass(expected_type, (int, float)):
        raise TypeError(f"Expected type was not a float. Got {expected_type}")

    try:
        query_value = expected_type(query_arg)
    except ValueError:
        query_value = default

    if autoupdate:
        _wrap_on_change_with_qs_update(key, kwargs)
    return st.number_input(label, value=query_value, key=key, **kwargs)



@overload
def from_query_args(key: str, default: str = "", *, as_list: Literal[False] = False) -> str:
    ...


@overload
def from_query_args(key: str, default: List[str], *, as_list: Literal[True]) -> List[str]:
    ...


def from_query_args(key: str, default: str | List[str] = "", *, as_list: bool = False) -> str | List[str]:
    """Return the value passed to the webpage URL via the query string for the given key.

    If the key does not exist in the query string, default is returned.
    Values are returned as python strings, unless as_list is True. If as_list is True, the values
    returned are lists of strings.
    If multiple values are defined for a given key, this code will throw an exception
    when as_list is False and will return all defined values when as_list is true.
    """
    query_args = st.experimental_get_query_params()
    value = query_args.get(key, default if as_list else [default])  # type: ignore  # overloads handle this
    if as_list:
        return value
    elif len(value) > 1:
        raise ValueError(f"Got multiple values for query string key {key}. Query contents: \n\n {query_args}")
    return value[0]


def from_query_args_index(key: str, options: Sequence[str], default: int = 0) -> int:
    """Return the index in the sequence "options" of the value given for the key in the URL query string.

    If the value is not present in the sequence "options", or if multiple values are provided, returns the default
    value. This can be used to create a selectbox with a default choice.

    >>> st.selectbox("my box", [1, 2, 3], stu.from_query_args_index("myoption", [1, 2, 3]))
    """
    try:
        return options.index(from_query_args(key, as_list=False))
    except ValueError:
        return default


def make_query_string(keys: Collection[str] | None = None, regex: Collection[str | re.Pattern] = ()) -> str:
    """Get a (relative) URL for a query string of of user-keyed fields on the page and their current values.

    Usage:
        >>> permalink = stu.make_query_string({"a", "b", "c"})
        >>> st.markdown(f"[permalink]({permalink})")

    Args:
        keys (optional, set[str]): The set of keys to be included in the query string.
        regex (optional, sequence[Pattern]): an optional set of patterns to match with keys as an alternate method of
            specifying which keys to include.

    Returns:
        url (str): the relative URL string (everything after the "?")

    Note: This method does NOT guarantee that the URL will return you to this exact session state, as
    only fields which are watching for a default value from the query string will autopopulate when someone navigates
    to the URL. When called without arguments, the query string will include values for fields which MAY NOT be watching
    the query string for values. These will be silently ignored.

    Note: Calling this method will only capture values for fields which have already been rendered, in other words, for
    >>> stu.make_query_string()
    >>> stu.number_input_gs("Hello", key="mykey")
    the make_query_string() call will not always capture the value of "mykey" because the streamlit application has not
    yet processed that line. At other times it may capture the value of mykey, but the value captured may be "stale"
    or out-of-date.
    """
    return "?" + urllib.parse.urlencode(_qs_intersect(keys, regex), doseq=True)


def update_qs_callback(keys: Collection[str] | None = None, regex: Collection[str | re.Pattern] = ()):
    """Return a callable that populates the browser URL with keys-value pairs for the user-defined keys specified.

    Accepts the same arguments as make_query_string.

    Usage:
        >>> st.button("Update URL!", on_click=stu.update_qs_callback(["field1", "field2"]))

    Args:
        keys (optional, set[str]): The set of keys to be included in the query string.
        regex (optional, sequence[Pattern]): an optional set of patterns to match with keys as an alternate method of
            specifying which keys to include.

    CAUTION: ----------------
    This callback returned by this function should ONLY be used inside a button's "on_click" or a form element's
    "on_change" argument. Due to how it interacts with elements that get data from the query string, calling the
    callback function at either the top or bottom of your script -- in the "main flow" -- can result either in
    query strings not working at all or elements that require multiple page refreshes in order to update,
    which can be frustrating for the user.

    Disregard at your own risk.
    ------------------------

    Note: This method does NOT guarantee that the URL will return you to this exact session state, as
    only fields which are watching for a default value from the query string will autopopulate when someone navigates
    to the URL. When called without arguments, the query string will include values for fields which MAY NOT be watching
    the query string for values. These will be silently ignored.
    """

    def _update_qs_callback():
        st.experimental_set_query_params(**_qs_intersect(keys, regex))

    return _update_qs_callback


def clear_qs_callback():
    """Clear the query string from the URL.

    CAUTION: This WILL revert every field that uses the query string back to its default value.
    """
    return st.experimental_set_query_params


def add_qs_callback(keys: Collection[str], regex: Collection[str | re.Pattern] = ()):
    """Return a callable that updates the browser URL with keys-value pairs for the user-defined keys specified.

    Accepts the same arguments as make_query_string. Existing key-value pairs in the URL are not changed or removed.

    Args:
        keys (set[str]): The set of keys to be added to the query string.
        regex (optional, sequence[Pattern]): an optional set of patterns to match with keys as an alternate method of
            specifying which keys to add.

    CAUTION: ----------------
    This callback returned by this function should ONLY be used inside a button's "on_click" or a form element's
    "on_change" argument. Due to how it interacts with elements that get data from the query string, calling the
    callback function at either the top or bottom of your script -- in the "main flow" -- can result either in
    query strings not working at all or elements that require multiple page refreshes in order to update,
    which can be frustrating for the user.

    Disregard at your own risk.
    ------------------------

    Note: This method does NOT guarantee that the URL will return you to this exact session state, as
    only fields which are watching for a default value from the query string will autopopulate when someone navigates
    to the URL.
    """

    def _add_qs_callback():
        existing_dict = st.experimental_get_query_params()
        existing_dict.update(_qs_intersect(keys, regex))
        st.experimental_set_query_params(**existing_dict)

    return _add_qs_callback



# Helper Functions -----------------------------------------------------------------------------

def _qs_intersect(keys: Collection[str] | None, regex: Collection[str | re.Pattern]) -> Mapping:
    """Smol helper function for Query String utilities."""
    if isinstance(keys, str) or isinstance(regex, str):
        raise ValueError("Arguments to query string functions must be non-str collections, e.g. list, tuple, set ...")
    # Keys are guaranteed to always be strs by SessionStateProxy
    session_keys = cast(KeysView[str], st.session_state.keys())
    if keys is None and not regex:
        use_keys = set(session_keys)
    else:
        # Find keys in session_keys that match the regex
        reg_keys = {key for key in session_keys if any(re.match(pattern, key) for pattern in regex)}
        # Put the intersection of the string keys and the reg keys together
        use_keys = (set(keys).intersection(session_keys) if keys else set()) | reg_keys

    # Return the new query string dictionary, but filter out blacklisted keys and empty values
    return {
        key: st.session_state[key] for key in use_keys if key not in QS_BLACKLIST_KEYS and st.session_state[key] != ""
    }
    

def _wrap_on_change_with_qs_update(key: str, kwargs: MutableMapping):
    """SMOL helper that adds a query string update for the specified key to the on_change arguments of kwargs."""
    existing_callback: Callable | None = kwargs.get("on_change", None)

    # Use the existing function if there's not one already defined for on_change.
    if existing_callback is None:
        kwargs["on_change"] = add_qs_callback(keys=(key,))
        return
    elif not callable(existing_callback):
        raise TypeError(f"'on_change' keyword argument is not callable: {existing_callback}")

    # Otherwise decorate the existing function with an update to the query params beforehand
    @functools.wraps(existing_callback)
    def wrapper():
        existing_dict = st.experimental_get_query_params()
        existing_dict.update(_qs_intersect(keys=(key,), regex=tuple()))
        st.experimental_set_query_params(**existing_dict)
        existing_callback()

    # At the end, mutate kwargs
    kwargs["on_change"] = wrapper
