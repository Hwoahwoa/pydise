from io import StringIO
import pytest
import pydise.detector
import jinja2


template_for = jinja2.Template(
    """
for {{ loop }}:
    print("foo")
"""
)
template_for_else = jinja2.Template(
    """
for {{ loop }}:
    {{ break_pass }}
else:
    print("foo")
"""
)

list_loop_true = [
    "i in range(5)",
    "i in ['foo']",
    "i in {'foo': 'bar'}.items()",
]

list_loop_false = [
    "i in range(0)",
    "i in []",
    "i in {}",
]

expected_for = ":3 -> Side effects detected :"
expected_for_else = ":5 -> Side effects detected :"


@pytest.mark.parametrize("loop_true", list_loop_true)
def test_for_else_iter_ok_no_break(loop_true):
    code_test = jinja2.Template.render(
        template_for_else, loop=loop_true, break_pass="pass"
    )

    test_parse = StringIO(code_test)

    with pytest.raises(pydise.detector.PydiseSideEffects) as exc_info:
        pydise_object = pydise.detector.PyDise(file=test_parse)
        pydise_object.analyze()
        pydise_object.notify(on_error="raise")

    assert expected_for_else in str(exc_info.value)


@pytest.mark.parametrize("loop_true", list_loop_true)
def test_for_else_iter_ok_break(loop_true):
    code_test = jinja2.Template.render(
        template_for_else, loop=loop_true, break_pass="break"
    )

    test_parse = StringIO(code_test)

    pydise_object = pydise.detector.PyDise(file=test_parse)
    pydise_object.analyze()
    pydise_object.notify(on_error="raise")


@pytest.mark.parametrize("loop_false", list_loop_false)
def test_for_else_iter_ko(loop_false):
    code_test = jinja2.Template.render(
        template_for_else, loop=loop_false, break_pass="break"
    )

    test_parse = StringIO(code_test)

    with pytest.raises(pydise.detector.PydiseSideEffects) as exc_info:
        pydise_object = pydise.detector.PyDise(file=test_parse)
        pydise_object.analyze()
        pydise_object.notify(on_error="raise")

    assert expected_for_else in str(exc_info.value)


@pytest.mark.parametrize("loop_true", list_loop_true)
def test_for_iter_ok(loop_true):
    code_test = jinja2.Template.render(template_for, loop=loop_true)

    test_parse = StringIO(code_test)

    with pytest.raises(pydise.detector.PydiseSideEffects) as exc_info:
        pydise_object = pydise.detector.PyDise(file=test_parse)
        pydise_object.analyze()
        pydise_object.notify(on_error="raise")

    assert expected_for in str(exc_info.value)


@pytest.mark.parametrize("loop_false", list_loop_false)
def test_for_iter_ko(loop_false):
    code_test = jinja2.Template.render(template_for, loop=loop_false)

    test_parse = StringIO(code_test)

    pydise_object = pydise.detector.PyDise(file=test_parse)
    pydise_object.analyze()
    pydise_object.notify(on_error="raise")


def test_try_ko():
    code_test = """
try:
    print("foo")
except Exception:
    pass
"""

    test_parse = StringIO(code_test)

    with pytest.raises(pydise.detector.PydiseSideEffects) as exc_info:
        pydise_object = pydise.detector.PyDise(file=test_parse)
        pydise_object.analyze()
        pydise_object.notify(on_error="raise")

    assert ":3 -> Side effects detected" in str(exc_info.value)


def test_try_ok():
    code_test = """
try:
    pass
except Exception:
    print("foo")
"""

    test_parse = StringIO(code_test)

    pydise_object = pydise.detector.PyDise(file=test_parse)
    pydise_object.analyze()
    pydise_object.notify(on_error="raise")


@pytest.mark.skip(reason="Not Implemented")
def test_except_ko():
    code_test = """
try:
    a = a
except NameError:
    print("foo")
"""

    test_parse = StringIO(code_test)

    with pytest.raises(pydise.detector.PydiseSideEffects) as exc_info:
        pydise_object = pydise.detector.PyDise(file=test_parse)
        pydise_object.analyze()
        pydise_object.notify(on_error="raise")

    assert ":3 -> Side effects detected" in str(exc_info.value)


def test_except_ok():
    code_test = """
try:
    a = a
except NameError:
    pass
"""

    test_parse = StringIO(code_test)

    pydise_object = pydise.detector.PyDise(file=test_parse)
    pydise_object.analyze()
    pydise_object.notify(on_error="raise")
