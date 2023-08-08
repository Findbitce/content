import pytest
from unittest.mock import patch
from HuntingFromIndicatorLayout import hunting_from_indicator_layout
import demistomock as demisto


@pytest.fixture
def mock_executeCommand():
    with patch('demistomock.executeCommand') as mock:
        yield mock


@pytest.mark.parametrize("sdo_value, expected_result",
                         [("indicator", "Proactive Threat Hunting Incident Created: Threat Hunting Session - indicator")])
def test_hunting_from_indicator_layout_success(mock_executeCommand, sdo_value, expected_result):
    mock_executeCommand.return_value = [{'Type': 1, 'Contents': 'Incident created successfully'}]

    result = hunting_from_indicator_layout(sdo_value)

    assert result.readable_output == expected_result


def test_main_no_indicator():
    args = {}
    demisto.args.return_value = args

    with pytest.raises(DemistoException, match="The automation was not executed from indicator layout"):
        main()


if __name__ == '__main__':
    pytest.main()
