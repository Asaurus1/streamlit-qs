from enum import Enum
from typing import Any, Dict
import unittest.mock as mock

import pytest
import streamlit as st
from streamlit.errors import StreamlitAPIException, StreamlitAPIWarning

import streamlit_qs as stqs


@pytest.fixture
def session_state():
    with mock.patch("streamlit.session_state", new={}) as ss:  # type: ignore
        yield ss


@pytest.fixture
def mock_get():
    with mock.patch("streamlit_qs.get_query_params", spec=stqs.get_query_params) as mock_get:
        yield mock_get


@pytest.fixture
def mock_set():
    with mock.patch("streamlit.experimental_set_query_params", spec=st.experimental_set_query_params) as mock_set:
        yield mock_set


@pytest.fixture
def mock_from_query_args():
    with mock.patch("streamlit_qs.from_query_args") as mock_from_query_args:
        yield mock_from_query_args


@pytest.fixture
def mock_query_args_index():
    with mock.patch("streamlit_qs.from_query_args_index") as mock_from_query_args_index:
        yield mock_from_query_args_index


@mock.patch("streamlit.commands.query_params.get_script_run_ctx")
def test_from_query_args_str(mock_ctx: mock.MagicMock):
    mock_ctx().query_string = "a=1&b=2&c=3&c=4"
    deflist = ["default"]
    stqs.from_query_args("a") == "1"
    stqs.from_query_args("b", "default") == "2"
    stqs.from_query_args("b", None) == "2"
    stqs.from_query_args("c", deflist, as_list=True) == ["3", "4"]
    stqs.from_query_args("d", "default") == "default"
    stqs.from_query_args("d", None) is None
    stqs.from_query_args("e", deflist, as_list=True) is deflist
    with pytest.raises(ValueError):
        stqs.from_query_args("c", "5") != ["3", "4"]  # type: ignore


@mock.patch("streamlit.commands.query_params.get_script_run_ctx")
def test_from_query_args_nonstr(mock_ctx: mock.MagicMock):
    mock_ctx().query_string = "a=1&b=2&c=3&c=4"
    stqs.from_query_args("a", unformat_func=int) == 1
    stqs.from_query_args("b", "default", unformat_func=int) == 2
    stqs.from_query_args("c", [5], as_list=True, unformat_func=int) == [3, 4]
    stqs.from_query_args("d", 5, unformat_func=int) == 5


def test_from_query_args_index_str(mock_from_query_args: mock.MagicMock):
    mock_from_query_args.return_value = "1"
    options = ["3", "1", "5"]
    stqs.from_query_args_index("a", options) == 1
    mock_from_query_args.return_value = "10"
    stqs.from_query_args_index("b", options, default=99) == 99
    stqs.from_query_args_index("b", options, default=None) == None


def test_from_query_args_index_nonstr(mock_from_query_args: mock.MagicMock):
    mock_from_query_args.return_value = 1
    options = [3, 1, 5]
    stqs.from_query_args_index("a", options, unformat_func=int) == 1
    mock_from_query_args.return_value = 10
    stqs.from_query_args_index("b", options, default=99, unformat_func=int) == 99


def test_selectbox_qs(mock_query_args_index: mock.MagicMock, session_state):
    mock_query_args_index.return_value = 1
    stqs.selectbox_qs("Test", ["a", "b", "c"], key="test")
    assert session_state["test"] == "b"
    mock_query_args_index.assert_called_with("test", ["a", "b", "c"], default=0, unformat_func=str)
    stqs.selectbox_qs("Test", [1, 2, 3], key="test2", unformat_func=int)
    assert session_state["test2"] == 2
    mock_query_args_index.assert_called_with("test2", [1, 2, 3], default=0, unformat_func=int)

    assert _test_helper_autoupdate(stqs.selectbox_qs, "Test", ["a", "b", "c"], key="test3", autoupdate=True)
    assert session_state["test3"] == "b"

    with pytest.raises(TypeError):
        # can't call without key
        stqs.selectbox_qs("Test", [1, 2, 3])  # type: ignore

    with pytest.raises(StreamlitAPIException):
        stqs.selectbox_qs("Test", options=[1, 2, None], key="badtest")


def test_radio_qs(mock_query_args_index: mock.MagicMock, session_state):
    mock_query_args_index.return_value = 1
    stqs.radio_qs("Test", ["a", "b", "c"], key="test")
    assert session_state["test"] == "b"
    mock_query_args_index.assert_called_with("test", ["a", "b", "c"], default=0, unformat_func=str)
    stqs.radio_qs("Test", [1, 2, 3], key="test2", unformat_func=int) == 2
    mock_query_args_index.assert_called_with("test2", [1, 2, 3], default=0, unformat_func=int)

    assert _test_helper_autoupdate(stqs.radio_qs, "Test", ["a", "b", "c"], key="test3", autoupdate=True)
    assert session_state["test3"] == "b"

    with pytest.raises(TypeError):
        # can't call without key
        stqs.radio_qs("Test", [1, 2, 3])  # type: ignore

    with pytest.raises(StreamlitAPIException):
        stqs.radio_qs("Test", options=[1, 2, None], key="badtest")


@mock.patch("streamlit.multiselect", wraps=st.multiselect)
def test_multiselect_qs_strings(mock_ms: mock.MagicMock, mock_from_query_args: mock.MagicMock, session_state):
    options = ["3", "1", "5"]

    mock_from_query_args.return_value = ["1"]
    stqs.multiselect_qs("Test", options, key="test")
    assert session_state["test"] == ["1"]
    mock_ms.assert_called_with("Test", options, default=None, key="test")

    mock_from_query_args.return_value = ["1", "5", "7"]
    stqs.multiselect_qs("Test", options, key="test2")
    assert session_state["test2"] == ["1", "5"]
    mock_ms.assert_called_with("Test", options, default=None, key="test2")

    mock_from_query_args.return_value = ["1", "3"]
    stqs.multiselect_qs("Test", options, default=["1", "3"], key="test3")
    "test3" not in session_state
    mock_ms.assert_called_with("Test", options, default=["1", "3"], key="test3")

    mock_from_query_args.return_value = ["3"]
    stqs.multiselect_qs("Test", options, default="3", key="test4")
    mock_ms.assert_called_with("Test", options, default="3", key="test4")

    mock_from_query_args.return_value = []
    stqs.multiselect_qs("Test", options, key="test5")
    mock_ms.assert_called_with("Test", options, default=None, key="test5")

    mock_from_query_args.return_value = []
    _test_helper_autoupdate(stqs.multiselect_qs, "Test", options, key="test6", autoupdate=True)

    mock_from_query_args.return_value = ["1", "5", "7"]
    with pytest.raises(ValueError):
        stqs.multiselect_qs("Test", options, key="test7", discard_missing=False) != ["1", "5"]

    with pytest.raises(TypeError):
        # can't call without key
        stqs.multiselect_qs("Test", ["1", "2", "3"])  # type: ignore


@mock.patch("streamlit.multiselect", wraps=st.multiselect)
def test_multiselect_qs_nonstring(mock_ms: mock.MagicMock, mock_from_query_args: mock.MagicMock, session_state):
    options = [1, 3, 5]

    mock_from_query_args.return_value = [1]
    stqs.multiselect_qs("Test", options, key="test", unformat_func=int)
    assert session_state["test"] == [1]
    mock_ms.assert_called_with("Test", options, default=None, key="test")

    mock_from_query_args.return_value = [1, 2, 3]
    stqs.multiselect_qs("Test", options, key="test2", unformat_func=lambda x: len(x))
    assert session_state["test2"] == [1, 3]
    mock_ms.assert_called_with("Test", options, default=None, key="test2")

    mock_from_query_args.return_value = [1, 5]
    stqs.multiselect_qs("Test", options, default=[1, 5], key="test3")
    "test3" not in session_state
    mock_ms.assert_called_with("Test", options, default=[1, 5], key="test3")

    mock_from_query_args.return_value = []
    stqs.multiselect_qs("Test", options, key="test4")
    mock_ms.assert_called_with("Test", options, default=None, key="test4")

    with pytest.raises(StreamlitAPIException):
        stqs.multiselect_qs("Test", options=[1, 2, None], key="badtest")


def test_checkbox_qs(mock_from_query_args: mock.MagicMock, session_state):
    for val in ("1", "True", "tRue", "TRUE"):
        mock_from_query_args.return_value = stqs._convert_bool_checkbox(val, False)
        stqs.checkbox_qs("Test", key="test")
        assert session_state["test"] is True
    for val in ("0", "FALSE", "False", "false"):
        mock_from_query_args.return_value = stqs._convert_bool_checkbox(val, False)
        stqs.checkbox_qs("Test", key="test2")
        assert session_state["test2"] is False

    mock_from_query_args.return_value = stqs._convert_bool_checkbox("TROO", True)
    stqs.checkbox_qs("Test", key="test3", default=True)
    assert session_state["test3"] is True
    mock_from_query_args.return_value = stqs._convert_bool_checkbox("TROO", False)
    stqs.checkbox_qs("Test", key="test4", default=False)
    assert session_state["test4"] is False
    
    mock_from_query_args.return_value = False
    _test_helper_autoupdate(stqs.checkbox_qs, "Test", key="test5", autoupdate=True)
    assert session_state["test5"] is False

    with pytest.raises(TypeError):
        # can't call without key
        stqs.selectbox_qs("Test", [1, 2])  # type: ignore


def test_text_input_qs(mock_from_query_args: mock.MagicMock, session_state):
    mock_from_query_args.return_value = "hello"
    stqs.text_input_qs("Test", default="world", key="test")
    assert session_state["test"] == "hello"
    mock_from_query_args.assert_called_with("test", default="world")

    _test_helper_autoupdate(stqs.text_input_qs, "Test", key="test2", autoupdate=True)
    assert session_state["test2"] == "hello"

    mock_from_query_args.side_effect = ValueError("multiple values")
    with pytest.raises(ValueError):
        stqs.text_input_qs("Test", key="a")
    with pytest.raises(TypeError):
        # can't call without key
        stqs.text_input_qs("Test", [1, 2])  # type: ignore


def test_text_area_qs(mock_from_query_args, session_state):
    mock_from_query_args.return_value = "hello"
    stqs.text_area_qs("Test", default="world", key="test")
    assert session_state["test"] == "hello"
    mock_from_query_args.assert_called_with("test", default="world")

    _test_helper_autoupdate(stqs.text_area_qs, "Test", key="test2", autoupdate=True)
    assert session_state["test2"] == "hello"

    mock_from_query_args.side_effect = ValueError("multiple values")
    with pytest.raises(ValueError):
        stqs.text_area_qs("Test", key="a")
    with pytest.raises(TypeError):
        # can't call without key
        stqs.text_area_qs("Test")  # type: ignore


def test_number_input_qs(mock_from_query_args, session_state):
    mock_from_query_args.return_value = "hello"
    val = stqs.number_input_qs("Test", default=4, key="test0")
    # When query string invalid and default=="min" we dont expect session_state to get set
    assert "test0" not in session_state
    assert val == 4 and isinstance(val, int)

    mock_from_query_args.return_value = "hello"
    val = stqs.number_input_qs("Test", key="test1")
    # When query string invalid and default=="min" we dont expect session_state to get set
    assert "test1" not in session_state
    assert val == 0.0 and isinstance(val, float)

    mock_from_query_args.return_value = "6"
    stqs.number_input_qs("Test", default=5.0, key="test2")
    val = session_state["test2"]
    assert val == 6.0 and isinstance(val, float)
    stqs.number_input_qs("Test", default=4, key="test3")
    val = session_state["test3"]
    assert val == 6 and isinstance(val, int)
    stqs.number_input_qs("Test", min_value=5, key="test4")
    val = session_state["test4"]
    assert val == 6 and isinstance(val, int)
    stqs.number_input_qs("Test", max_value=7, key="test5")
    val = session_state["test5"]
    assert val == 6 and isinstance(val, int)
    stqs.number_input_qs("Test", max_value=4, key="test5.1")  # it even lets you go outside normal bounds?
    val = session_state["test5.1"]
    assert val == 6 and isinstance(val, int)
    stqs.number_input_qs("Test", step=4.5, key="test6")
    val = session_state["test6"]
    assert val == 6.0 and isinstance(val, float)
    stqs.number_input_qs("Test", key="test7")
    val = session_state["test7"]
    assert val == 6.0 and isinstance(val, float)

    stqs.number_input_qs("Test", default=None, key="test8")
    val = session_state["test8"]
    assert val == 6.0 and isinstance(val, float)

    mock_from_query_args.return_value = "NOT_A_NUMBER"
    assert _test_helper_autoupdate(stqs.number_input_qs, "Test", key="test9", autoupdate=True) == 0
    assert "test9" not in session_state
    assert stqs.number_input_qs("Test", default=None, key="test10") is None
    assert "test10" not in session_state

    mock_from_query_args.return_value = None
    assert stqs.number_input_qs("Test", key="test11") == 0
    assert "test11" not in session_state
    assert stqs.number_input_qs("Test", default=5.0, key="test12") == 5.0
    assert "test12" not in session_state
    assert stqs.number_input_qs("Test", max_value=5, key="test13") == 0
    assert "test13" not in session_state

    mock_from_query_args.side_effect = ValueError("multiple values")
    with pytest.raises(ValueError):
        stqs.number_input_qs("Test", key="a")

    mock_from_query_args.side_effect = None
    mock_from_query_args.return_value = "6"
    with pytest.raises(TypeError, match="Expected type was not a float"):
        stqs.number_input_qs("Test", min_value="string", key="test")  # bad type with no default
    with pytest.raises(TypeError, match="Expected type was not a float"):
        stqs.number_input_qs("Test", max_value="string", key="test")  # bad type with no default
    with pytest.raises(TypeError, match="Expected type was not a float"):
        stqs.number_input_qs("Test", step="string", key="test")  # bad type with no default
    with pytest.raises(TypeError, match="keyword-only"):
        # can't call without key
        stqs.number_input_qs("Test")  # type: ignore


def test_qs_intersect():
    new_session_state1 = {"a3": 1, "b3": 2, "b2": 3}
    with mock.patch("streamlit.session_state", new=new_session_state1):
        stqs._qs_intersect(None, tuple()) == new_session_state1
        stqs._qs_intersect(tuple(), tuple()) == {}  # i.e. if the user passes in keys=[]
        stqs._qs_intersect(["a3", "b3"], tuple()) == {"a3": 1, "b3": 2}
        stqs._qs_intersect(["a3", "badval"], tuple()) == {"a3": 1}
        stqs._qs_intersect(None, ["b.$"]) == {"b2": 3, "b3": 2}
        stqs._qs_intersect(["a3"], ["b.$"]) == {"a3": 1, "b2": 3, "b3": 2}

    new_session_state2 = {"a3": 1, "blacklisted_key": "blacklisted"}
    with mock.patch("streamlit.session_state", new=new_session_state2):
        stqs.blacklist_key("blacklisted_key")
        stqs._qs_intersect(None, tuple()) == {"a3": 1}
        stqs.unblacklist_key("blacklisted_key")
        assert "blacklisted_key" not in stqs.QS_BLACKLIST_KEYS

    with pytest.raises(ValueError, match="Arguments to query string functions must be non-str collections"):
        stqs._qs_intersect("foo", tuple())
    with pytest.raises(ValueError, match="Arguments to query string functions must be non-str collections"):
        stqs._qs_intersect(None, "foo")


def test_make_query_string(session_state):
    session_state.update({"a3": 1, "b3": "hello world", "b2": 3})
    assert all(kv in stqs.make_query_string() for kv in ["?", "a3=1", "b3=hello+world", "b2=3"])
    assert all(kv in stqs.make_query_string(regex=["b.$"]) for kv in ["?", "b3=hello+world", "b2=3"])
    stqs.make_query_string(["b3"]) == "?b3=hello+world"


def test_set_qs_callback(mock_set, session_state):
    session_state.update({"a3": 1, "b3": "hello world", "b2": 3})

    func = stqs.set_qs_callback(["a3", "b3"], regex=[])
    mock_set.assert_not_called()
    func()
    mock_set.assert_called_with(a3=1, b3="hello world")
    mock_set.reset_mock()

    assert stqs.set_qs_callback()() is None
    mock_set.assert_called_with(a3=1, b3="hello world", b2=3)
    mock_set.reset_mock()


def test_add_qs_callback(mock_get, mock_set, session_state):
    session_state.update({"a3": 1, "b3": "hello world", "b2": 3, "nonekey": None})

    mock_get.return_value = {"a1": "hi", "nonekey": "5"}
    func = stqs.add_qs_callback(["b2"], regex=[])
    mock_set.assert_not_called()
    func()
    mock_set.assert_called_with(a1="hi", b2=3, nonekey="5")

    assert stqs.add_qs_callback(["nonekey"])() is None
    mock_set.assert_called_with(a1="hi", b2=3, nonekey="5")
    mock_set.reset_mock()


def test_update_qs_callback(mock_get, mock_set, session_state):
    session_state.update({"a3": 1, "b3": "hello world", "b2": 3, "nonekey": None})

    mock_get.return_value = {"a1": "hi", "nonekey": "5"}
    func = stqs.update_qs_callback(["b2"], regex=[])
    mock_set.assert_not_called()
    func()
    mock_set.assert_called_with(a1="hi", b2=3, nonekey="5")

    assert stqs.update_qs_callback(["nonekey"])() is None
    mock_set.assert_called_with(a1="hi", b2=3)
    mock_set.reset_mock()

    assert stqs.update_qs_callback()() is None
    mock_set.assert_called_with(a1="hi", b2=3, b3="hello world", a3=1)
    mock_set.reset_mock()


def test_clear_qs_callback(mock_get, mock_set, session_state):
    session_state.update({"a3": 1, "b3": "hello world", "b2": 3, "nonekey": None})

    func = stqs.clear_qs_callback()
    mock_set.assert_not_called()
    func()
    mock_set.assert_called_once()
    mock_set.reset_mock()

    mock_get.return_value = {"a1": "hi", "b3": "world"}
    assert stqs.clear_qs_callback(["b3"])() is None
    mock_set.assert_called_with(a1="hi")


def test_wrap_on_chage_with_qs_update(mock_get, mock_set, session_state):
    kwargs: Any = {"foo": "a", "bar": "b", "none": None}
    stqs._wrap_on_change_with_qs_update("key", kwargs, remove_none_values=False)
    assert callable(kwargs["on_change"])
    assert kwargs["on_change"].__name__ == "_add_qs_callback"
    mock_get.assert_not_called()
    mock_set.assert_not_called()
    mock_get.return_value = {"key": "hi"}
    kwargs["on_change"]()
    mock_set.assert_called_with(key="hi")
    mock_set.reset_mock()
    mock_get.reset_mock()

    callback = mock.MagicMock(__name__="mockfunction")
    kwargs = {"foo": "a", "bar": "b", "on_change": callback}
    stqs._wrap_on_change_with_qs_update("key", kwargs, remove_none_values=True)
    assert callable(kwargs["on_change"])
    assert kwargs["on_change"].__name__ == "mockfunction"
    assert kwargs["on_change"] is not callback
    callback.assert_not_called()
    mock_get.assert_not_called()
    mock_set.assert_not_called()
    mock_get.return_value = {"key": "a", "foobar": "b"}
    session_state["key"] = None
    kwargs["on_change"]()
    callback.assert_called()
    mock_set.assert_called_with(foobar="b")
    mock_set.reset_mock()

    kwargs = {"foo": "a", "bar": "b", "on_change": 1}
    with pytest.raises(TypeError, match="keyword argument is not callable"):
        stqs._wrap_on_change_with_qs_update("key", kwargs, remove_none_values=True)


def _test_helper_autoupdate(func, *args, **kwargs):
    """Helper function to test an "autoupdate" call"""

    # patch the wrap on change function
    with mock.patch("streamlit_qs._wrap_on_change_with_qs_update") as mock_wrap:
        # Add autoupdate=True as a kwarg if it hasn't been by the caller
        kwargs.update(autoupdate=True)
        # Call the function under test
        retval = func(*args, **kwargs)
        # assert that wrap_on_change was called
        mock_wrap.assert_called()
    # Return whatever was returned by the function under test
    return retval


def test_unenumifier():
    class AnEnum(Enum):
        FOO = 0
        BAR = 1

    class NotAnEnum:
        ...

    unenumifier = stqs.unenumifier(AnEnum)
    assert callable(unenumifier)
    assert unenumifier("FOO") == AnEnum.FOO
    assert unenumifier("AnEnum.BAR") == AnEnum.BAR
    with pytest.raises(ValueError):
        unenumifier("invalid")
    with pytest.raises(AttributeError):
        stqs.unenumifier("foo")  # type: ignore
    with pytest.raises(TypeError):
        stqs.unenumifier(NotAnEnum)("FOO")  # type: ignore


def test_ensure_list():
    assert stqs._ensure_list("abc") == ["abc"]
    assert stqs._ensure_list(b"abc") == [b"abc"]
    assert stqs._ensure_list((5, 6, 7)) == [5, 6, 7]
    assert stqs._ensure_list([1, 2, 3]) == [1, 2, 3]
    assert stqs._ensure_list(5) == [5]


def test_infer_unformat_func():
    class AnEnum(Enum):
        FOO = 0
        BAR = 1

    assert stqs._infer_common_unformat_funcs([1, 2, 3], str) is int
    assert stqs._infer_common_unformat_funcs([1.0, 2.0, 3.0], str) is float
    assert stqs._infer_common_unformat_funcs([AnEnum.FOO, AnEnum.BAR], str).__name__ == "_unenum_AnEnum"

    assert stqs._infer_common_unformat_funcs([1, 2, 3.0], str) is str
    assert stqs._infer_common_unformat_funcs([1.0, 2.0, AnEnum.FOO], str) is str
    assert stqs._infer_common_unformat_funcs([AnEnum.FOO, AnEnum.BAR, "AnEnum.BAZ"], str) is str

    assert stqs._infer_common_unformat_funcs([1, 2, 3], float) is float
    assert stqs._infer_common_unformat_funcs([1.0, 2.0, 3.0], int) is int
    def enum_unformat(e): return e.name
    assert stqs._infer_common_unformat_funcs([AnEnum.FOO, AnEnum.BAR], enum_unformat) is enum_unformat


@mock.patch("streamlit.exception")
def test_warn_on_common_unmatching_unformat_funcs(mock_warning):
    stqs._warn_on_common_unmatching_unformat_functions([1, 2, 3], str)
    assert isinstance(mock_warning.call_args[0][0], StreamlitAPIWarning)
    assert repr({int}) in str(mock_warning.call_args[0][0])

    stqs._warn_on_common_unmatching_unformat_functions([1, 2.0, "str"], str)
    assert isinstance(mock_warning.call_args[0][0], StreamlitAPIWarning)
    assert repr({int, float, str}) in str(mock_warning.call_args[0][0])

    stqs._warn_on_common_unmatching_unformat_functions([StreamlitAPIException(), StreamlitAPIWarning()], str)
    assert isinstance(mock_warning.call_args[0][0], StreamlitAPIWarning)
    assert repr({StreamlitAPIException, StreamlitAPIWarning}) in str(mock_warning.call_args[0][0])

    mock_warning.reset_mock()  # remaining tests should NOT call this
    stqs._warn_on_common_unmatching_unformat_functions([StreamlitAPIException(), StreamlitAPIWarning()], int)
    stqs._warn_on_common_unmatching_unformat_functions([1, 2.0, "str"], float)
    stqs._warn_on_common_unmatching_unformat_functions([1, 2, 3], float)
    stqs._warn_on_common_unmatching_unformat_functions([1, 2, 3], int)
    mock_warning.assert_not_called()
