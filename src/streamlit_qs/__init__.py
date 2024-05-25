"""Query string extensions for Streamlit."""
from __future__ import annotations
from enum import Enum

import functools
import json
import re
import urllib.parse
from typing import TYPE_CHECKING, Any, Callable, Collection, KeysView, List, Mapping, MutableMapping, Sequence, Set, Type, TypeVar, cast, overload
from typing_extensions import Literal

import streamlit as st
from streamlit.errors import StreamlitAPIException, StreamlitAPIWarning
from streamlit.type_util import OptionSequence, ensure_indexable

if TYPE_CHECKING:
    Number = int | float
    from streamlit.elements.widgets.slider import SliderValue


# TypeVars
T = TypeVar("T")
Tenum = TypeVar("Tenum", bound=Enum)
Tbs = TypeVar("Tbs", bytes, str)


# Settings/Constants
DISABLE_WARNINGS = False
"""This flag controls the display of warning message for common problems.
Set to false if you know what you're doing."""


QS_BLACKLIST_KEYS: Set[str] = set()
"""A list of query string keys are are not allowed because they are used elsewhere in application
backend code. Expected to be set by the user at application initalization."""


def blacklist_key(key: str):
    """Add a key to the list of blacklisted keys that won't show up in the query string."""
    QS_BLACKLIST_KEYS.add(key)


def unblacklist_key(key: str):
    """Remove a key from the list of blacklisted keys that won't show up in the query string.

    Key is ignored if it isn't already blacklisted.
    """
    QS_BLACKLIST_KEYS.discard(key)


# Start of the "_qs" functions
def selectbox_qs(
    label: str,
    options: OptionSequence[T],
    index: int | None = 0,
    *,
    key: str,
    autoupdate: bool = False,
    unformat_func: Any = str,
    **kwargs
) -> T | None:
    """Create a streamlit selectbox which automatically populates itself from the URL query string.

    Takes all arguments that st.selectbox takes, but the "key" keyword argument _must_ be provided. Returns the value
    selected by the user.
    """
    indexible_options = ensure_indexable(options)
    _raise_if_option_is_none(indexible_options, widgettype="selectbox_qs")

    query_index = from_query_args_index(key, options, default=index, unformat_func=unformat_func)
    if query_index is not None and key not in st.session_state:
        st.session_state.setdefault(key, indexible_options[query_index])
    if autoupdate:
        _wrap_on_change_with_qs_update(key, kwargs, remove_none_values=(index is None))

    return st.selectbox(label, options, index=index, key=key, **kwargs)


def radio_qs(
    label: str,
    options: OptionSequence[T],
    index: int | None = 0,
    *,
    key: str,
    autoupdate: bool = False,
    unformat_func: Any = str,
    **kwargs
) -> T | None:
    """Create a streamlit radio widget which automatically populates itself from the URL query string.

    Takes all arguments that st.radio takes, but the "key" keyword argument _must_ be provided. Returns the value
    selected by the user. "autoupdate" causes that value to also be populated into the URL query string on change.
    """
    indexible_options = ensure_indexable(options)
    _raise_if_option_is_none(indexible_options, widgettype="radio_qs")

    query_index=from_query_args_index(key, options, default=index, unformat_func=unformat_func)
    if query_index is not None and key not in st.session_state:
        st.session_state.setdefault(key, indexible_options[query_index])
    if autoupdate:
        _wrap_on_change_with_qs_update(key, kwargs, remove_none_values=(index is None))

    return st.radio(label, options, index=query_index, key=key, **kwargs)


def multiselect_qs(
    label: str,
    options: OptionSequence[T],
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
    indexible_options = ensure_indexable(options)
    _raise_if_option_is_none(indexible_options, widgettype="multiselect_qs")

    default_list: List[T] = [] if default is None else _ensure_list(default)
    maybe_from_query = from_query_args(key, default=default_list, as_list=True, unformat_func=unformat_func)

    ms_default_subset = [item for item in maybe_from_query if item in indexible_options]

    # discard missing items or throw an exception if we got a value from the query string that is not in the options
    if not discard_missing and ms_default_subset != maybe_from_query:
        raise ValueError(
            "Some query string options were not contained in the available options for multiselect "
            f'key = "{key}". Missing values: {[item for item in maybe_from_query if item not in indexible_options]}'
        )
    if maybe_from_query != default_list:
        # Set session state IF we're not using the default value.
        st.session_state.setdefault(key, ms_default_subset)
    if autoupdate:
        _wrap_on_change_with_qs_update(key, kwargs, remove_none_values=(default is None))
    return st.multiselect(label, options, default=default, key=key, **kwargs)


def checkbox_qs(label: str, default: bool = False, *, key: str, autoupdate: bool = False, **kwargs) -> bool:
    """Create a streamlit checkbox widget which automatically populates itself from the URL query string.

    Takes all arguments that st.checkbox takes, but the "key" keyword argument _must_ be provided.
    The following values will be treated as True: "true", "1" (case insensitive)
    The following values will be treated as False: "false", "0" (case insensitive)
    Any other value will result in the checkbox using the "default" value.

    "autoupdate" causes that value to also be populated into the URL query string on change.
    """
    query_bool = from_query_args(key, default=default, unformat_func=lambda val: _convert_bool_checkbox(val, default=default))
    st.session_state.setdefault(key, query_bool)
    if autoupdate:
        _wrap_on_change_with_qs_update(key, kwargs, remove_none_values=(default is None))
    return st.checkbox(label, value=default, key=key, **kwargs)


def toggle_qs(label: str, default: bool = False, *, key: str, autoupdate: bool = False, **kwargs) -> bool:
    """Create a streamlit toggle widget which automatically populates itself from the URL query string.

    Takes all arguments that st.toggle takes, but the "key" keyword argument _must_ be provided.
    The following values will be treated as True: "true", "1" (case insensitive)
    The following values will be treated as False: "false", "0" (case insensitive)
    Any other value will result in the toggle using the "default" value.

    "autoupdate" causes that value to also be populated into the URL query string on change.
    """
    query_bool = from_query_args(key, default=default, unformat_func=lambda val: _convert_bool_checkbox(val, default=default))
    st.session_state.setdefault(key, query_bool)
    if autoupdate:
        _wrap_on_change_with_qs_update(key, kwargs, remove_none_values=(default is None))
    return st.toggle(label, value=default, key=key, **kwargs)


@overload
def text_input_qs(label: str, default: None, *, key: str, autoupdate: bool = False, **kwargs) -> str | None: ...

@overload
def text_input_qs(label: str, default: str = "", *, key: str, autoupdate: bool = False, **kwargs) -> str: ...

def text_input_qs(label: str, default: str | None = "", *, key: str, autoupdate: bool = False, **kwargs) -> str | None:
    """Create a streamlit text_input which automatically populates itself from the URL query string.

    Takes all arguments that st.text_input takes, but the "key" keyword argument _must_ be provided. Returns the value
    selected by the user. "autoupdate" causes that value to also be populated into the URL query string on change.
    """
    st.session_state.setdefault(key, from_query_args(key, default=default))
    if autoupdate:
        _wrap_on_change_with_qs_update(key, kwargs, remove_none_values=(default is None))
    return st.text_input(label, value=default, key=key, **kwargs)


@overload
def text_area_qs(label: str, default: None, *, key: str, autoupdate: bool = False, **kwargs) -> str | None: ...

@overload
def text_area_qs(label: str, default: str = "", *, key: str, autoupdate: bool = False, **kwargs) -> str: ...

def text_area_qs(label: str, default: str | None = "", *, key: str, autoupdate: bool = False, **kwargs) -> str | None:
    """Create a streamlit text_area which automatically populates itself from the URL query string.

    Takes all arguments that st.text_area takes, but the "key" keyword argument _must_ be provided. Returns the value
    selected by the user. "autoupdate" causes that value to also be populated into the URL query string on change.
    """
    st.session_state.setdefault(key, from_query_args(key, default=default))
    if autoupdate:
        _wrap_on_change_with_qs_update(key, kwargs, remove_none_values=(default is None))
    return st.text_area(label, value=default, key=key, **kwargs)


@overload
def number_input_qs(label: str, default: Number | Literal["min"] = "min", *, key: str, autoupdate: bool = False, **kwargs) -> Number:
    ...

@overload
def number_input_qs(label: str, default: Number | None  = None, *, key: str, autoupdate: bool = False, **kwargs) -> Number | None:
    ...

def number_input_qs(label: str, default = "min", *, key: str, autoupdate: bool = False, **kwargs) -> Number | None:
    """Create a streamlit number_input which automatically populates itself from the URL query string.

    Takes all arguments that st.number_input takes, but the "key" keyword argument _must_ be provided. Returns the value
    selected by the user. "autoupdate" causes that value to also be populated into the URL query string on change.
    """
    query_value: Number | None | Literal["min"]

    # Get the query string value and attempt to coerce it to an int or float depending on
    # the arguments to this function, in a similar way that number_input changes from an int
    # widget to a float widget depending on the types here.
    # If this works, we set up session_state with the value we got from the url, otherwise
    # we just do nothing and call the regular number_input function (with a possible wrapped
    # autoupdate callback).
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
        st.session_state.setdefault(key, query_value)
    except (ValueError, TypeError):
        pass

    if autoupdate:
        _wrap_on_change_with_qs_update(key, kwargs, remove_none_values=(default is None))
    return st.number_input(label, value=default, key=key, **kwargs)


@overload
def from_query_args(key: str, default: str = "", *, as_list: Literal[False] = False, unformat_func: Any = str) -> str:
    ...


@overload
def from_query_args(key: str, default: T, *, unformat_func: Any, as_list: Literal[False] = False) -> T:
    ...

@overload
def from_query_args(key: str, default: None, *, as_list: Literal[False] = False, unformat_func: Any = str) -> Any:
    # actually returns an Optional[str] but mypy won't let us do that until https://github.com/python/mypy/pull/15846
    # is released in 1.5.2.
    ...

@overload
def from_query_args(key: str, default: List[str], *, as_list: Literal[True], unformat_func: Any = str) -> List[str]:
    ...

@overload
def from_query_args(key: str, default: List[None], *, as_list: Literal[True], unformat_func: Any = str) -> Any:
    # actually returns a List[Optional[str]] but mypy won't let us do that until
    # https://github.com/python/mypy/pull/15846 is released in 1.5.2
    ...

@overload
def from_query_args(key: str, default: List[T], *, as_list: Literal[True], unformat_func: Any) -> List[T]:
    ...

def from_query_args(key, default = "", *, as_list=False, unformat_func: Any = str):
    """Return the value passed to the webpage URL via the query string for the given key.

    If the key does not exist in the query string, default is returned.
    Values are returned as a single python object, unless as_list is True. If as_list is True, the values
    returned are lists of objects. By default all objects are strings. The `unformat_func` argument takes
    a callable that converts a single `str` to type `T` and can be used to parse serialized data into
    python objects.

    If multiple values are defined for a given key, this code will throw an exception when as_list is False
    and will return all defined values when as_list is true.
    """
    values = st.query_params.get_all(key)

    if not values:
        # if there's nothing in the query string, give the default
        out_value = default if as_list else [default]
    elif unformat_func is str:
        # Otherwise the list of values from the query string as strings
        out_value = values  # values is always str and user expects str
    else:
        # Or possibly convert them first
        out_value = [unformat_func(val) for val in values]  # convert str -> T using unformat_func

    if as_list:
        return out_value
    if len(out_value) > 1:
        raise ValueError(f"Got multiple values for query string key {key}. Query contents: \n\n {st.query_params.to_dict()}")

    return out_value[0]


@overload
def from_query_args_index(key: str, options: OptionSequence[T], default: int = 0, unformat_func: Any = str) -> int:
    ...

@overload
def from_query_args_index(key: str, options: OptionSequence[T], default: None, unformat_func: Any = str) -> int | None:
    ...

def from_query_args_index(key: str, options: OptionSequence[T], default: int | None = 0, unformat_func: Any = str) -> int | None:
    """Return the index in the sequence "options" of the value given for the key in the URL query string.

    If the value is not present in the sequence "options", or if multiple values are provided, returns the default
    value. This can be used to create a selectbox with a default choice.

    >>> st.selectbox("my box", [1, 2, 3], stu.from_query_args_index("myoption", [1, 2, 3]))
    """
    indexible_options = ensure_indexable(options)
    unformat_func = _infer_common_unformat_funcs(indexible_options, unformat_func)
    try:
        return indexible_options.index(from_query_args(key, as_list=False, unformat_func=unformat_func))
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


def set_qs_callback(keys: Collection[str] | None = None, regex: Collection[str | re.Pattern] = ()) -> Callable[[], None]:
    """Return a callable that replaces the browser URL query string with keys-value pairs for the user-defined keys specified.

    Usage:
        >>> st.button("Update URL!", on_click=stu.set_qs_callback(["field1", "field2"]))

    Args:
        keys (optional, set[str]): The set of keys to be included in the query string.
        regex (optional, sequence[Pattern]): an optional set of patterns to match with keys as an alternate method of
            specifying which keys to include.


    Note: This method does NOT guarantee that the URL will return you to this exact session state, as only fields
    which are watching for a default value from the query string will autopopulate when someone navigates to the URL.
    When called without arguments, the query string will include values for fields which MAY NOT be watching the query
    string for values. These will be silently ignored.
    """

    def _set_qs_callback():
        st.query_params.clear()
        st.query_params.update(_qs_intersect(keys, regex))

    return _set_qs_callback


def clear_qs_callback(keys: Collection[str] | None = None, regex: Collection[str | re.Pattern] = ()) -> Callable[[], None]:
    """Return a callable that clears the query string from the URL. If a specific set of keys or patterns are provided,
    only those keys will be cleared. This callback is designed to be used with the "on_click" or "on_change" argument
    of a button or widget.

    This will NOT reset the values of any fields that depend on the query string, you must do that yourself by
    removing the fields' keys from `st.session_state`.

    Args:
        keys (set[str]): The set of keys to be removed to the query string.
        regex (optional, sequence[Pattern]): an optional set of patterns to match with keys as an alternate method of
            specifying which keys to add.
    """

    if hasattr(st.query_params, "from_dict"):
        # Streamlit 1.34.0
        def _clear_qs_callback():
            if not keys and not regex:
                st.query_params.clear()
            else:
                clear_dict = {k: st.query_params.get_all(k) for k in st.query_params if k not in _qs_intersect(keys, regex)}
                st.query_params.from_dict(clear_dict)
    else:
        # Streamlit 1.33 and earlier (less efficient)
        def _clear_qs_callback():
            if not keys and not regex:
                st.query_params.clear()
            else:
                for key in _qs_intersect(keys, regex).keys():
                    st.query_params.pop(key, None)

    return _clear_qs_callback


def add_qs_callback(keys: Collection[str] | None = None, regex: Collection[str | re.Pattern] = ()) -> Callable[[], None]:
    """Return a callable that adds to the browser URL the keys-value pairs for the user-defined keys specified.
    Keys with a None value are ignored. Existing key-value pairs in the URL will not be changed or removed
    (they may be reordered). This callback is designed to be used with the "on_click" or "on_change" argument
    of a button or widget.

    Args:
        keys (optional, set[str]): The set of keys to be added to the query string.
        regex (optional, sequence[Pattern]): an optional set of patterns to match with keys as an alternate method of
            specifying which keys to add.

    Note: This method does NOT guarantee that the URL will return you to this exact session state, as only fields
    which are watching for a default value from the query string will autopopulate when someone navigates to the URL.
    When called without arguments, the query string will include values for fields which MAY NOT be watching the query
    string for values. These will be silently ignored.
    """

    def _add_qs_callback():
        st.query_params.update(_qs_intersect(keys, regex))

    return _add_qs_callback


def update_qs_callback(keys: Collection[str] | None = None, regex: Collection[str | re.Pattern] = ()) -> Callable[[], None]:
    """Return a callable that updates the browser URL with keys-value pairs for the user-defined keys specified.
    Keys which are paired with a None value are *removed* from the query string. Other existing key-value pairs
    in the URL will not be changed or removed (they may be reordered). This callback is designed to be used with
    the "on_click" or "on_change" argument of a button or widget.

    Args:
        keys (optional, set[str]): The set of keys to be added to the query string.
        regex (optional, sequence[Pattern]): an optional set of patterns to match with keys as an alternate method of
            specifying which keys to add.

    Note: This method does NOT guarantee that the URL will return you to this exact session state, as only fields
    which are watching for a default value from the query string will autopopulate when someone navigates to the URL.
    When called without arguments, the query string will include values for fields which MAY NOT be watching the query
    string for values. These will be silently ignored.
    """

    if hasattr(st.query_params, "from_dict"):
        # Streamlit 1.34.0
        def _update_qs_callback():
            new_dict = _qs_intersect(keys, regex, allownone=True)
            update_dict = {k: st.query_params.get_all(k) for k in st.query_params}
            for key, value in new_dict.items():
                if value is not None:
                    update_dict[key] = value
                elif key in update_dict:
                    del update_dict[key]
            st.query_params.from_dict(update_dict)  # type: ignore  # doesn't accept a list[str] right now
    else:
        # Streamlit 1.33 and earlier (less efficient)
        def _update_qs_callback():
            new_dict = _qs_intersect(keys, regex, allownone=True)
            update_dict = {}
            for key, value in new_dict.items():
                if value is not None:
                    update_dict[key] = value
                elif key in update_dict:
                    st.query_params.pop(key)
            st.query_params.update(update_dict)

    return _update_qs_callback



def unenumifier(cls: Type[Tenum]) -> Callable[[str], Tenum] :
    """Get a factory function for turning strings into enum members.

    Python's default Enums render as strings as "<cls>.<member>". This function
    returns a callable that looks up the member based on this string.
    """
    def _unenum(value: str) -> Tenum:
        """Convert a string into a member of {cls}"""
        value_name = value.replace(cls.__name__ + ".", "")
        try:
            return cls[value_name]
        except KeyError:
            raise ValueError(f"'{value_name} is not a valid member of '{cls.__qualname__}'")

    _unenum.__name__ += "_" + cls.__name__
    _unenum.__doc__ = _unenum.__doc__.format(cls=cls)  # type: ignore

    return _unenum


# Helper Functions -----------------------------------------------------------------------------

def _qs_intersect(keys: Collection[str] | None, regex: Collection[str | re.Pattern], allownone: bool = False) -> Mapping[str, Any]:
    """Get a dictionary containing pairs from st.session_state whose keys match the arguments/patterns."""
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

    # Return the new query string dictionary, but filter out blacklisted keys and None values
    return {
        key: st.session_state[key] for key in use_keys if key not in QS_BLACKLIST_KEYS and (allownone or st.session_state[key] is not None)
    }


def _wrap_on_change_with_qs_update(key: str, kwargs: MutableMapping, remove_none_values: bool):
    """Mutates kwargs to add a query string update for the specified key to the on_change argument."""
    existing_callback: Callable | None = kwargs.get("on_change", None)

    # Select the right kind of callback
    if remove_none_values:
        pre_update_func = update_qs_callback(keys=(key,))
    else:
        pre_update_func = add_qs_callback(keys=(key,))

    # Use the existing function if there's not one already defined for on_change.
    if existing_callback is None:
        kwargs["on_change"] = pre_update_func
        return
    if not callable(existing_callback):
        raise TypeError(f"'on_change' keyword argument is not callable: {existing_callback}")

    # Otherwise decorate the existing function with an update to the query params beforehand
    @functools.wraps(existing_callback)
    def wrapper(*args, **kwargs):
        pre_update_func()
        existing_callback(*args, **kwargs)

    # At the end, mutate kwargs
    kwargs["on_change"] = wrapper


def _convert_bool_checkbox(string_bool: str, default: bool) -> bool:
    """Convert from string values to boolean values, with a default value if conversion fails."""
    if string_bool.lower() in ("1", "true"):
        return True
    if string_bool.lower() in ("0", "false"):
        return False
    return default


@overload
def _ensure_list(maybe_list: Tbs) -> List[Tbs]:
    ...

@overload
def _ensure_list(maybe_list: Sequence[T]) -> List[T]:
    ...

@overload
def _ensure_list(maybe_list: T) -> List[T]:
    ...

def _ensure_list(maybe_list):
    """Convert single values and sequences (except bytes and str) to lists."""
    if isinstance(maybe_list, list):
        return maybe_list
    if isinstance(maybe_list, (bytes, str)) or not isinstance(maybe_list, Sequence):
        return [maybe_list]
    return list(maybe_list)


def _infer_common_unformat_funcs(indexible_options: Sequence[Any], unformat_func):
    """Infers some common unformat_funcs based on the items in the indexible_options and returns the new function."""
    if unformat_func is str and len(indexible_options)!=0 and not all(isinstance(opt, str) for opt in indexible_options):
        # If they're ints or floats or bytes (uniformly), coerce back to those.
        for typ in (int, float, bytes):
            if all(isinstance(opt, typ) for opt in indexible_options):
                return typ

        # If they all come from the same enum, coerce back to that
        if isinstance(indexible_options[0], Enum):
            enum_cls = indexible_options[0].__class__
            if all(isinstance(opt, enum_cls) for opt in indexible_options):
                return unenumifier(enum_cls)

    _warn_on_common_unmatching_unformat_functions(indexible_options, unformat_func)
    return unformat_func


def _warn_on_common_unmatching_unformat_functions(options, unformat_func):
    """Produces a warning if the user registers non-string options but provides or leaves the
    default "str" as an unformat_func."""
    if DISABLE_WARNINGS:
        return
    if not all(isinstance(opt, str) for opt in options) and unformat_func is str:
        detected_types = {type(opt) for opt in options}
        msg = f"""In the widget below, you've used a select or multi-select streamlit_qs element
with non-string-type options (we found {detected_types}), but did not provide an `unformat_func`
to deserialize the values from the URL back into those objects, and we could not deduce one for you.
For example, you may have tried something like

    st.selectbox_qs("Pick a number", options=[1, 1.5, 2], key="picknumber")

To do this correctly, you need to explicitly specify how to convert the values in the URL back to options.
In this case you might define a function like

    def int_or_float(string):
        try: return int(string)
        except ValueError: pass
        return float(string)

And then call

    st.selectbox_qs("Pick a number", options=[1, 1.5, 2], key="pickanumber", unformat_func=int_or_float)

    """
        # pylint: disable=protected-access
        st.exception(StreamlitAPIWarning(msg))
        st._logger.get_logger(__name__).warning(msg, stack_info=True, stacklevel=5)


def _raise_if_option_is_none(indexible_options, widgettype="widget that supports section from a list of options"):
    """Raises an exception if the user tries to pass None as an option. While this is technically allowed
    with the base streamlit widgets, we can't serialize "None" to the URL string in a way that is differentiable
    from the string "None" as well as the None value that some widgets can now return in Streamlit 1.27.0+. So we
    must disallow it."""
    if any(opt is None for opt in indexible_options):
        msg = f"""You may not pass the value None as an item to a streamlit_qs {widgettype}, as there is no reliable
way to serialize this value to the URL query string. If you are trying to create a widget with an empty default value,
please pass None as the 'default' argument instead of adding to the 'options' list.

Got the following options: {indexible_options}
        """
        raise StreamlitAPIException(msg)
