from io import StringIO
import pytest
import pydise.detector
import jinja2

template_while = jinja2.Template(
    """
while {{ condition }}:
    print("foo")
"""
)
template_while_else = jinja2.Template(
    """
while {{ condition }}:
    pass
else:
    print("foo")
"""
)

template_if = jinja2.Template(
    """
if {{ condition }}:
    print("foo")
"""
)
expected_if = ":3 -> Side effects detected :"
expected_while = ":3 -> Side effects detected :"
expected_while_else = ":5 -> Side effects detected :"

list_conditions_true = [
    "True",
    "False or True",
    "True and True",
    "True == True",
    "True != False",
    '"1"',
    '"1" or ""',
    '"1" and "1"',
    '"1" == "1"',
    '"1" != ""',
    "1",
    "1 or 0",
    "1 and 1",
    "1 == 1",
    "1 != 0",
    '"a" in ["a"]',
    '"a" not in ["b"]',
    "1 in [1]",
    "1 not in [0]",
    '["a", "b"] == ["a", "b"]',
    '["a", "b"] != ["b", "a"]',
    "True and (True == True) and 1==1",
    "True and (True == True) or 2==1",
    "(True and (True != True)) or 1==1",
]

list_conditions_false = [
    "False",
    "False and True",
    "False or False",
    "True == False",
    "False != False",
    '""',
    '"" or ""',
    '"1" and ""',
    '"1" == ""',
    '"1" != "1"',
    "0",
    "0 or 0",
    "1 and 0",
    "1 == 2",
    "1 != 1",
    '"a" in ["b"]',
    '"a" not in ["a"]',
    "1 in []",
    "1 not in [1]",
    '["a", "b"] != ["a", "b"]',
    '["a", "b"] == ["b", "a"]',
    "True and (True == True) and 2==1",
    "True and (True == False) or 2==1",
    "(True and (True != True)) or 2==1",
]


@pytest.mark.parametrize("condition_true", list_conditions_true)
def test_if_ko(condition_true):
    code_test = jinja2.Template.render(template_if, condition=condition_true)

    test_parse = StringIO(code_test)

    with pytest.raises(pydise.detector.PydiseSideEffects) as exc_info:
        pydise_object = pydise.detector.PyDise(file=test_parse)
        pydise_object.analyze()
        pydise_object.notify(on_error="raise")

    assert expected_if in str(exc_info.value)


@pytest.mark.parametrize("condition_false", list_conditions_false)
def test_if_ok(condition_false):
    code_test = jinja2.Template.render(template_if, condition=condition_false)

    test_parse = StringIO(code_test)

    pydise_object = pydise.detector.PyDise(file=test_parse)
    pydise_object.analyze()
    pydise_object.notify(on_error="raise")


@pytest.mark.parametrize("condition_true", list_conditions_true)
def test_while_iter_ok(condition_true):
    code_test = jinja2.Template.render(template_while, condition=condition_true)

    test_parse = StringIO(code_test)

    with pytest.raises(pydise.detector.PydiseSideEffects) as exc_info:
        pydise_object = pydise.detector.PyDise(file=test_parse)
        pydise_object.analyze()
        pydise_object.notify(on_error="raise")

    assert expected_while in str(exc_info.value)


@pytest.mark.parametrize("condition_false", list_conditions_false)
def test_while_iter_ko(condition_false):
    code_test = jinja2.Template.render(template_while, condition=condition_false)

    test_parse = StringIO(code_test)

    pydise_object = pydise.detector.PyDise(file=test_parse)
    pydise_object.analyze()
    pydise_object.notify(on_error="raise")


@pytest.mark.parametrize("condition_false", list_conditions_false)
def test_while_else_iter_ko(condition_false):
    code_test = jinja2.Template.render(template_while_else, condition=condition_false)

    test_parse = StringIO(code_test)

    with pytest.raises(pydise.detector.PydiseSideEffects) as exc_info:
        pydise_object = pydise.detector.PyDise(file=test_parse)
        pydise_object.analyze()
        pydise_object.notify(on_error="raise")

    assert expected_while_else in str(exc_info.value)
