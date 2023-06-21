from io import StringIO
import ast
import pytest
import itertools
import pydise.detector
import jinja2

template_condition_simple = jinja2.Template("""
if {{ condition }}:
    print("foo")   
""")
expected_condition_simple = "print at line '3'"
list_conditions_simple_ko = ['True',
                             'False or True',
                             'True and True',
                             'True == True',
                             'True != False',
                             '"1"',
                             '"1" or ""',
                             '"1" and "1"',
                             '"1" == "1"',
                             '"1" != ""',
                             '1',
                             '1 or 0',
                             '1 and 1',
                             '1 == 1',
                             '1 != 0',
                             '"a" in ["a"]',
                             '"a" not in ["b"]',
                             '1 in [1]',
                             '1 not in [0]',
                             '["a", "b"] == ["a", "b"]',
                             '["a", "b"] != ["b", "a"]']

list_conditions_simple_ok = ['False',
                             'False and True',
                             'False or False',
                             'True == False',
                             'False != False',
                             '""',
                             '"" or ""',
                             '"1" and ""',
                             '"1" == ""',
                             '"1" != "1"',
                             '0',
                             '0 or 0',
                             '1 and 0',
                             '1 == 2',
                             '1 != 1',
                             '"a" in ["b"]',
                             '"a" not in ["a"]',
                             '1 in []',
                             '1 not in [1]',
                             '["a", "b"] != ["a", "b"]',
                             '["a", "b"] == ["b", "a"]']


@pytest.mark.parametrize("condition_ko", list_conditions_simple_ko)
def test_if_ko(condition_ko):
    code_test = jinja2.Template.render(template_condition_simple, condition=condition_ko)

    test_parse = StringIO(code_test)

    with pytest.raises(pydise.detector.PydiseSideEffects) as exc_info:
        pydise_object = pydise.detector.PyDise(file=test_parse)
        pydise_object.analyze()
        pydise_object.notify(on_error="raise")

    assert str(exc_info.value) == expected_condition_simple


@pytest.mark.parametrize("condition_ok", list_conditions_simple_ok)
def test_if_ok(condition_ok):
    code_test = jinja2.Template.render(template_condition_simple, condition=condition_ok)

    test_parse = StringIO(code_test)

    pydise_object = pydise.detector.PyDise(file=test_parse)
    pydise_object.analyze()
    pydise_object.notify(on_error="raise")
