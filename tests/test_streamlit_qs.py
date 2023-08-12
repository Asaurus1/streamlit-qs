from enum import Enum
from typing import Any
import unittest.mock as mock

import pytest
import streamlit as st
from streamlit.errors import StreamlitAPIException

import streamlit_qs as stu


@mock.patch("streamlit.commands.query_params.get_script_run_ctx")
def test_from_query_args_str(mock_ctx: mock.MagicMock):
    mock_ctx().query_string = "a=1&b=2&c=3&c=4"
    deflist = ["default"]
    assert stu.from_query_args("a") == "1"
    assert stu.from_query_args("b", "default") == "2"
    assert stu.from_query_args("c", deflist, as_list=True) == ["3", "4"]
    assert stu.from_query_args("d", "default") == "default"
    assert stu.from_query_args("e", deflist, as_list=True) is deflist
    with pytest.raises(ValueError):
        assert stu.from_query_args("c", "5") != ["3", "4"]  # type: ignore


@mock.patch("streamlit.commands.query_params.get_script_run_ctx")
def test_from_query_args_nonstr(mock_ctx: mock.MagicMock):
    mock_ctx().query_string = "a=1&b=2&c=3&c=4"
    assert stu.from_query_args("a", unformat_func=int) == 1
    assert stu.from_query_args("b", "default", unformat_func=int) == 2
    assert stu.from_query_args("c", [5], as_list=True, unformat_func=int) == [3, 4]
    assert stu.from_query_args("d", 5, unformat_func=int) == 5


@mock.patch("streamlit_qs.from_query_args")
def test_from_query_args_index_str(mock_from_query_args: mock.MagicMock):
    mock_from_query_args.return_value = "1"
    options = ["3", "1", "5"]
    assert stu.from_query_args_index("a", options) == 1
    mock_from_query_args.return_value = "10"
    assert stu.from_query_args_index("b", options, default=99) == 99


@mock.patch("streamlit_qs.from_query_args")
def test_from_query_args_index_nonstr(mock_from_query_args: mock.MagicMock):
    mock_from_query_args.return_value = "1"
    options = ["3", "1", "5"]
    assert stu.from_query_args_index("a", options) == 1
    mock_from_query_args.return_value = "10"
    assert stu.from_query_args_index("b", options, default=99) == 99


@mock.patch("streamlit_qs.from_query_args_index")
def test_selectbox_qs(mock_query_args_index: mock.MagicMock):
    mock_query_args_index.return_value = 1
    assert stu.selectbox_qs("Test", ["a", "b", "c"], key="test") == "b"
    mock_query_args_index.assert_called_with("test", ["a", "b", "c"], default=0, unformat_func=str)
    assert stu.selectbox_qs("Test", [1, 2, 3], key="test", unformat_func=int) == 2
    mock_query_args_index.assert_called_with("test", [1, 2, 3], default=0, unformat_func=int)

    assert _test_helper_autoupdate(stu.selectbox_qs, "Test", ["a", "b", "c"], key="test", autoupdate=True) == "b"

    with pytest.raises(TypeError):
        # can't call without key
        stu.selectbox_qs("Test", [1, 2, 3])  # type: ignore


@mock.patch("streamlit_qs.from_query_args_index")
def test_radio_qs(mock_query_args_index: mock.MagicMock):
    mock_query_args_index.return_value = 1
    assert stu.radio_qs("Test", ["a", "b", "c"], key="test") == "b"
    mock_query_args_index.assert_called_with("test", ["a", "b", "c"], default=0, unformat_func=str)
    assert stu.radio_qs("Test", [1, 2, 3], key="test", unformat_func=int) == 2
    mock_query_args_index.assert_called_with("test", [1, 2, 3], default=0, unformat_func=int)

    assert _test_helper_autoupdate(stu.radio_qs, "Test", ["a", "b", "c"], key="test", autoupdate=True) == "b"

    with pytest.raises(TypeError):
        # can't call without key
        stu.radio_qs("Test", [1, 2, 3])  # type: ignore


@mock.patch("streamlit_qs.from_query_args")
@mock.patch("streamlit.multiselect", wraps=st.multiselect)
def test_multiselect_qs_strings(mock_ms: mock.MagicMock, mock_from_query_args: mock.MagicMock):
    options = ["3", "1", "5"]

    mock_from_query_args.return_value = ["1"]
    assert stu.multiselect_qs("Test", options, key="test") == ["1"]
    mock_ms.assert_called_with("Test", options, default=["1"], key="test")

    mock_from_query_args.return_value = ["1", "5", "7"]
    assert stu.multiselect_qs("Test", options, key="test") == ["1", "5"]
    mock_ms.assert_called_with("Test", options, default=["1", "5"], key="test")

    mock_from_query_args.return_value = ["1", "3"]
    assert stu.multiselect_qs("Test", options, default=["1", "3"], key="test") == ["1", "3"]
    mock_ms.assert_called_with("Test", options, default=["1", "3"], key="test")

    mock_from_query_args.return_value = ["3"]
    assert stu.multiselect_qs("Test", options, default="3", key="test") == ["3"]
    mock_ms.assert_called_with("Test", options, default=["3"], key="test")

    mock_from_query_args.return_value = []
    assert stu.multiselect_qs("Test", options, key="test") == []
    mock_ms.assert_called_with("Test", options, default=[], key="test")

    mock_from_query_args.return_value = []
    assert _test_helper_autoupdate(stu.multiselect_qs, "Test", options, key="test", autoupdate=True) == []

    mock_from_query_args.return_value = ["1", "5", "7"]
    with pytest.raises(ValueError):
        assert stu.multiselect_qs("Test", options, key="test", discard_missing=False) != ["1", "5"]

    with pytest.raises(TypeError):
        # can't call without key
        stu.multiselect_qs("Test", [1, 2, 3])  # type: ignore


@mock.patch("streamlit_qs.from_query_args")
@mock.patch("streamlit.multiselect", wraps=st.multiselect)
def test_multiselect_qs_nonstring(mock_ms: mock.MagicMock, mock_from_query_args: mock.MagicMock):
    options = [1, 3, 5]

    mock_from_query_args.return_value = [1]
    assert stu.multiselect_qs("Test", options, key="test", unformat_func=int) == [1]
    mock_ms.assert_called_with("Test", options, default=[1], key="test")

    mock_from_query_args.return_value = [1, 2, 3]
    assert stu.multiselect_qs("Test", options, key="test", unformat_func=lambda x: len(x)) == [1, 3]
    mock_ms.assert_called_with("Test", options, default=[1, 3], key="test")

    mock_from_query_args.return_value = [1, 5]
    assert stu.multiselect_qs("Test", options, default=[1, 5], key="test") == [1, 5]
    mock_ms.assert_called_with("Test", options, default=[1, 5], key="test")

    mock_from_query_args.return_value = []
    assert stu.multiselect_qs("Test", options, key="test") == []
    mock_ms.assert_called_with("Test", options, default=[], key="test")


@mock.patch("streamlit_qs.from_query_args")
def test_checkbox_qs(mock_from_query_args: mock.MagicMock):
    for val in ("1", "True", "tRue", "TRUE"):
        mock_from_query_args.return_value = stu._convert_bool_checkbox(val, False)
        assert stu.checkbox_qs("Test", key="test") is True
    for val in ("0", "FALSE", "False", "false"):
        mock_from_query_args.return_value = stu._convert_bool_checkbox(val, False)
        assert stu.checkbox_qs("Test", key="test") is False

    mock_from_query_args.return_value = stu._convert_bool_checkbox("TROO", True)
    assert stu.checkbox_qs("Test", key="test", default=True) is True
    mock_from_query_args.return_value = stu._convert_bool_checkbox("TROO", False)
    assert stu.checkbox_qs("Test", key="test", default=False) is False
    
    mock_from_query_args.return_value = False
    assert _test_helper_autoupdate(stu.checkbox_qs, "Test", key="test", autoupdate=True) is False

    with pytest.raises(TypeError):
        # can't call without key
        stu.selectbox_qs("Test", [1, 2])  # type: ignore


@mock.patch("streamlit_qs.from_query_args")
def test_text_input_qs(mock_from_query_args: mock.MagicMock):
    mock_from_query_args.return_value = "hello"
    assert stu.text_input_qs("Test", default="world", key="test") == "hello"
    mock_from_query_args.assert_called_with("test", default="world")

    assert _test_helper_autoupdate(stu.text_input_qs, "Test", key="test", autoupdate=True) == "hello"

    mock_from_query_args.side_effect = ValueError("multiple values")
    with pytest.raises(ValueError):
        stu.text_input_qs("Test", key="a")
    with pytest.raises(TypeError):
        # can't call without key
        stu.text_input_qs("Test", [1, 2])  # type: ignore


@mock.patch("streamlit_qs.from_query_args")
def test_text_area_qs(mock_from_query_args):
    mock_from_query_args.return_value = "hello"
    assert stu.text_area_qs("Test", default="world", key="test") == "hello"
    mock_from_query_args.assert_called_with("test", default="world")

    assert _test_helper_autoupdate(stu.text_area_qs, "Test", key="test", autoupdate=True) == "hello"

    mock_from_query_args.side_effect = ValueError("multiple values")
    with pytest.raises(ValueError):
        stu.text_area_qs("Test", key="a")
    with pytest.raises(TypeError):
        # can't call without key
        stu.text_area_qs("Test")  # type: ignore


@mock.patch("streamlit_qs.from_query_args")
def test_number_input_qs(mock_from_query_args):
    mock_from_query_args.return_value = "hello"
    val = stu.number_input_qs("Test", default=4, key="test")
    assert val == 4 and isinstance(val, int)

    mock_from_query_args.return_value = "hello"
    val = stu.number_input_qs("Test", key="test")
    assert val == 0.0 and isinstance(val, float)

    mock_from_query_args.return_value = "6"
    val = stu.number_input_qs("Test", default=5.0, key="test")
    assert val == 6.0 and isinstance(val, float)
    val = stu.number_input_qs("Test", default=4, key="test")
    assert val == 6 and isinstance(val, int)
    val = stu.number_input_qs("Test", min_value=5, key="test")
    assert val == 6 and isinstance(val, int)
    val = stu.number_input_qs("Test", max_value=7, key="test")
    assert val == 6 and isinstance(val, int)
    val = stu.number_input_qs("Test", step=4.5, key="test")
    assert val == 6.0 and isinstance(val, float)
    val = stu.number_input_qs("Test", key="test")
    assert val == 6.0 and isinstance(val, float)

    mock_from_query_args.return_value = "NOT_A_NUMBER"
    assert _test_helper_autoupdate(stu.number_input_qs, "Test", key="test", autoupdate=True) == 0

    mock_from_query_args.side_effect = ValueError("multiple values")
    with pytest.raises(ValueError):
        stu.number_input_qs("Test", key="a")

    mock_from_query_args.side_effect = None
    mock_from_query_args.return_value = "6"
    with pytest.raises(TypeError, match="Expected type was not a float"):
        stu.number_input_qs("Test", min_value="string", key="test")  # bad type with no default
    with pytest.raises(TypeError, match="Expected type was not a float"):
        stu.number_input_qs("Test", max_value="string", key="test")  # bad type with no default
    with pytest.raises(TypeError, match="Expected type was not a float"):
        stu.number_input_qs("Test", step="string", key="test")  # bad type with no default
    with pytest.raises(StreamlitAPIException):
        stu.number_input_qs("Test", max_value=1.0, key="test")  # set value outside bounds
    with pytest.raises(TypeError, match="keyword-only"):
        # can't call without key
        stu.number_input_qs("Test")  # type: ignore


def test_qs_intersect():
    new_session_state1 = {"a3": 1, "b3": 2, "b2": 3}
    with mock.patch("streamlit.session_state", new=new_session_state1):
        assert stu._qs_intersect(None, tuple()) == new_session_state1
        assert stu._qs_intersect(tuple(), tuple()) == {}  # i.e. if the user passes in keys=[]
        assert stu._qs_intersect(["a3", "b3"], tuple()) == {"a3": 1, "b3": 2}
        assert stu._qs_intersect(["a3", "badval"], tuple()) == {"a3": 1}
        assert stu._qs_intersect(None, ["b.$"]) == {"b2": 3, "b3": 2}
        assert stu._qs_intersect(["a3"], ["b.$"]) == {"a3": 1, "b2": 3, "b3": 2}

    new_session_state2 = {"a3": 1, "blacklisted_key": "blacklisted"}
    with mock.patch("streamlit.session_state", new=new_session_state2):
        stu.blacklist_key("blacklisted_key")
        assert stu._qs_intersect(None, tuple()) == {"a3": 1}
        stu.unblacklist_key("blacklisted_key")
        assert "blacklisted_key" not in stu.QS_BLACKLIST_KEYS

    with pytest.raises(ValueError, match="Arguments to query string functions must be non-str collections"):
        stu._qs_intersect("foo", tuple())
    with pytest.raises(ValueError, match="Arguments to query string functions must be non-str collections"):
        stu._qs_intersect(None, "foo")


def test_make_query_string():
    new_session_state = {"a3": 1, "b3": "hello world", "b2": 3}
    with mock.patch("streamlit.session_state", new=new_session_state):
        assert all(kv in stu.make_query_string() for kv in ["?", "a3=1", "b3=hello+world", "b2=3"])
        assert all(kv in stu.make_query_string(regex=["b.$"]) for kv in ["?", "b3=hello+world", "b2=3"])
        assert stu.make_query_string(["b3"]) == "?b3=hello+world"


@mock.patch("streamlit.experimental_set_query_params", spec=st.experimental_set_query_params)
@mock.patch("streamlit.experimental_get_query_params", spec=st.experimental_set_query_params)
def test_update_and_add_qs_callback(mock_get, mock_set):
    new_session_state = {"a3": 1, "b3": "hello world", "b2": 3}
    with mock.patch("streamlit.session_state", new=new_session_state):
        func = stu.update_qs_callback(["a3", "b3"], regex=[])
        mock_set.assert_not_called()
        func()
        mock_set.assert_called_with(a3=1, b3="hello world")
        mock_set.reset_mock()

        mock_get.return_value = {"a1": "hi"}
        func = stu.add_qs_callback(["b2"], regex=[])
        mock_set.assert_not_called()
        func()
        mock_set.assert_called_with(a1="hi", b2=3)
        mock_set.reset_mock()


@mock.patch("streamlit.experimental_set_query_params", spec=st.experimental_set_query_params)
def test_clear_qs_callback(mock_set):
    stu.clear_qs_callback()()
    mock_set.assert_called_once()


@mock.patch("streamlit.experimental_set_query_params", spec=st.experimental_set_query_params)
@mock.patch("streamlit.experimental_get_query_params", spec=st.experimental_set_query_params)
def test_wrap_on_chage_with_qs_update(mock_get, mock_set):
    kwargs: Any = {"foo": "a", "bar": "b"}
    stu._wrap_on_change_with_qs_update("key", kwargs)
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
    stu._wrap_on_change_with_qs_update("key", kwargs)
    assert callable(kwargs["on_change"])
    assert kwargs["on_change"].__name__ == "mockfunction"
    assert kwargs["on_change"] is not callback
    callback.assert_not_called()
    mock_get.assert_not_called()
    mock_set.assert_not_called()
    mock_get.return_value = {"key": "hi"}
    kwargs["on_change"]()
    callback.assert_called()
    mock_set.assert_called_with(key="hi")
    mock_set.reset_mock()

    kwargs = {"foo": "a", "bar": "b", "on_change": 1}
    with pytest.raises(TypeError, match="keyword argument is not callable"):
        stu._wrap_on_change_with_qs_update("key", kwargs)


def _test_helper_autoupdate(func, *args, **kwargs):
    """Helper function to test an "autoupdate" call"""

    # patch the wrap on change function
    with mock.patch.object(stu, "_wrap_on_change_with_qs_update") as mock_wrap:
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

    unenumifier = stu.unenumifier(AnEnum)
    assert callable(unenumifier)
    assert unenumifier("FOO") == AnEnum.FOO
    assert unenumifier("AnEnum.BAR") == AnEnum.BAR
    with pytest.raises(ValueError):
        unenumifier("invalid")
    with pytest.raises(AttributeError):
        stu.unenumifier("foo")  # type: ignore
    with pytest.raises(TypeError):
        stu.unenumifier(NotAnEnum)("FOO")  # type: ignore


def test_ensure_list():
    assert stu._ensure_list("abc") == ["abc"]
    assert stu._ensure_list(b"abc") == [b"abc"]
    assert stu._ensure_list((5, 6, 7)) == [5, 6, 7]
    assert stu._ensure_list([1, 2, 3]) == [1, 2, 3]
    assert stu._ensure_list(5) == [5]
