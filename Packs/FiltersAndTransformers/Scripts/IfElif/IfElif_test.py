import demistomock as demisto
import pytest


@pytest.mark.parametrize(
    'expression, expected_result',
    [
        ('true and [1,2,3]', True),
        ('1 and 2 < 3 < 4 or 5 or [] or 4', True),
        ('1 or 2 or 0', True),
        ('false and {1: 2, 3: [4,5,6,7]}', False),
        ('regex_match("\s", " ")', True),
        ('regex_match("\s", "s")', False),
    ]
)
def test_parse_boolean_expression(expression, expected_result):
    """
    Given:
        - A boolean expression as a string.

    When:
        - Running If-Elif

    Then:
        - Parse the expression and return it's boolean value.
    """
    from IfElif import evaluate

    result = evaluate(expression)

    assert result is expected_result


@pytest.mark.parametrize(
    'expression',
    [
        'word or 1',
        '__import__("os").system("RM -RF /")',
        '1 if 0 else 2',
        'sys.exit()'
    ]
)
def test_parse_boolean_expression_error(expression):
    """
    Given:
        - A boolean expression with invalid or unsupported syntax.

    When:
        - Running If-Elif

    Then:
        - Raise an error.
    """
    from IfElif import evaluate

    with pytest.raises(SyntaxError):
        evaluate(expression)


def test_load_conditions(mocker):
    """
    Given:
        - A string containing context references in the format #{<path>} and/or "#VALUE".

    When:
        - Running If-Elif

    Then:
        - Replace #{...}'s with the string representation of the corresponding value in the context
          and "#VALUE" with the demisto.args()['value'].
    """
    import IfElif

    IfElif.ARGS = {
        'conditions': '{"key1": #{a.b.[0].c}, "key2": #VALUE}',
        'value': 'value2',
    }
    dt = mocker.patch.object(demisto, 'dt', return_value='value1')

    result = IfElif.load_conditions()

    assert result == {'key1': 'value1', 'key2': 'value2'}
    dt.assert_called_with({}, 'a.b.[0].c')
