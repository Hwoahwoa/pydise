from io import StringIO
import pytest
import pydise.detector

expected_error = ":1 -> Side effects detected :"
list_ko = [
    "print('foo')",
    "assert('foo')",
    "time.sleep(1)",
    "exit(0)",
    "a = lambda x: print(x); a('foo')",
]

list_ok = ["False", "a = 3", "a = lambda x: print(x)", "pass"]


@pytest.mark.parametrize("statement_ko", list_ko)
def test_base_ko(statement_ko):
    test_parse = StringIO(statement_ko)

    with pytest.raises(pydise.detector.PydiseSideEffects) as exc_info:
        pydise_object = pydise.detector.PyDise(file=test_parse)
        pydise_object.analyze()
        pydise_object.notify(on_error="raise")

    assert expected_error in str(exc_info.value)


@pytest.mark.parametrize("statement_ok", list_ok)
def test_base_ok(statement_ok):
    test_parse = StringIO(statement_ok)

    pydise_object = pydise.detector.PyDise(file=test_parse)
    pydise_object.analyze()
    pydise_object.notify(on_error="raise")
