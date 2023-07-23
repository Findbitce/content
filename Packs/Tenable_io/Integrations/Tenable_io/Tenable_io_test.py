import demistomock as demisto
import pytest
from freezegun import freeze_time
from CommonServerPython import *
import json
import requests
# type: ignore=operator

MOCK_PARAMS = {
    'access-key': 'fake_access_key',
    'secret-key': 'fake_access_key',
    'url': 'http://123-fake-api.com/',
    'unsecure': True,
    'proxy': True
}

MOCK_RAW_VULN_BY_ASSET = {
    'vulnerabilities': [
        {
            'count': 117,
            'plugin_family': 'General',
            'plugin_id': 51292,
            'plugin_name': 'Fake Plugin Name',
            'vulnerability_state': 'Resurfaced',
            'accepted_count': 0,
            'recasted_count': 0,
            'counts_by_severity': [
                {
                    'count': 117,
                    'value': 2
                }
            ],
            'severity': 2
        },
    ]
}

EXPECTED_VULN_BY_ASSET_RESULTS = [
    {
        'Id': 51292,
        'Name': 'Fake Plugin Name',
        'Severity': 'Medium',
        'Family': 'General',
        'VulnerabilityOccurences': 117,
        'VulnerabilityState': 'Resurfaced'
    }
]


class MockResponse:

    def __init__(self, json_data, status_code=200, content=None):
        self.json_data = json_data
        self.status_code = status_code
        self.content = content

    def json(self):
        return self.json_data

    def raise_for_status(self):
        pass


def load_json(filename):
    with open(f'test_data/{filename}.json') as f:
        return json.load(f)


def mock_demisto(mocker, mock_args=None):
    mocker.patch.object(demisto, 'params', return_value=MOCK_PARAMS)
    mocker.patch.object(demisto, 'args', return_value=mock_args)
    mocker.patch.object(demisto, 'uniqueFile', return_value='file')
    mocker.patch.object(demisto, 'investigation', return_value={'id': 'id'})
    mocker.patch.object(demisto, 'results')
    mocker.patch.object(demisto, 'debug')


def test_get_scan_status(mocker, requests_mock):
    mock_demisto(mocker, {'scanId': '25'})
    requests_mock.get(MOCK_PARAMS['url'] + 'scans/25', json={'info': {'status': 'canceled'}})

    from Tenable_io import get_scan_status_command
    results = get_scan_status_command()

    entry_context = results['EntryContext']['TenableIO.Scan(val.Id && val.Id === obj.Id)']

    assert 'Scan status for 25' in results['HumanReadable']
    assert entry_context['Id'] == '25'
    assert entry_context['Status'] == 'canceled'


def test_get_vuln_by_asset(mocker, requests_mock):
    mock_demisto(mocker, {'hostname': 'fake.hostname'})
    requests_mock.get(MOCK_PARAMS['url'] + 'workbenches/assets', json={'assets': [{'id': 'fake_asset_id'}]})
    requests_mock.get(MOCK_PARAMS['url'] + 'workbenches/assets/fake_asset_id/vulnerabilities/',
                      json=MOCK_RAW_VULN_BY_ASSET)

    from Tenable_io import get_vulnerabilities_by_asset_command
    results = get_vulnerabilities_by_asset_command()

    actual_result = results['EntryContext']['TenableIO.Vulnerabilities']

    for k in actual_result[0].keys():
        assert EXPECTED_VULN_BY_ASSET_RESULTS[0][k] == actual_result[0][k]


def test_pause_scan_command(mocker, requests_mock):
    mock_demisto(mocker, {'scanId': '25'})
    requests_mock.get(MOCK_PARAMS['url'] + 'scans/25', json={'info': {'status': 'running'}})
    requests_mock.post(MOCK_PARAMS['url'] + 'scans/25/pause', json={'info': {'status': 'running'}})

    from Tenable_io import pause_scan_command

    results = pause_scan_command()
    entry_context = results[0]['EntryContext']['TenableIO.Scan(val.Id && val.Id === obj.Id)']

    assert 'scan was paused successfully' in results[0]['HumanReadable']
    assert entry_context['Id'] == '25'
    assert entry_context['Status'] == 'Pausing'


def test_resume_scan_command(mocker, requests_mock):
    mock_demisto(mocker, {'scanId': '25'})
    requests_mock.get(MOCK_PARAMS['url'] + 'scans/25', json={'info': {'status': 'paused'}})
    requests_mock.post(MOCK_PARAMS['url'] + 'scans/25/resume', json={'info': {'status': 'paused'}})
    from Tenable_io import resume_scan_command

    results = resume_scan_command()
    entry_context = results[0]['EntryContext']['TenableIO.Scan(val.Id && val.Id === obj.Id)']

    assert 'scan was resumed successfully' in results[0]['HumanReadable']
    assert entry_context['Id'] == '25'
    assert entry_context['Status'] == 'Resuming'


def test_get_vulnerability_details_command(mocker, requests_mock):
    mock_demisto(mocker, {'vulnerabilityId': '1', 'dateRange': '3'})
    requests_mock.get(MOCK_PARAMS['url'] + 'workbenches/vulnerabilities/1/info',
                      json={'info': {'Id': '1'}})
    from Tenable_io import get_vulnerability_details_command

    results = get_vulnerability_details_command()
    entry_context = results['EntryContext']['TenableIO.Vulnerabilities']

    assert 'Vulnerability details' in results['HumanReadable']
    assert entry_context['Id'] == '1'


def test_get_scans_command(mocker, requests_mock):
    mock_demisto(mocker, {'folderId': '1'})
    requests_mock.get(MOCK_PARAMS['url'] + 'scans/?folder_id=1',
                      json={'scans': [{'status': 'running', 'id': '1'}],
                            'info': {'id': '1'}})
    requests_mock.get(MOCK_PARAMS['url'] + 'scans/1', json={'info': {'status': 'paused'}})

    from Tenable_io import get_scans_command

    results = get_scans_command()
    entry_context = results[0]['EntryContext']['TenableIO.Scan(val.Id && val.Id === obj.Id)']

    assert 'Tenable.io - List of Scans' in results[0]['HumanReadable']
    assert entry_context[0]['Id'] == '1'


def test_launch_scan_command(mocker, requests_mock):
    mock_demisto(mocker, {'scanId': '1', 'scanTargets': 'target1,target2'})
    requests_mock.get(MOCK_PARAMS['url'] + 'scans/1', json={'info': {'status': 'paused'}})
    requests_mock.post(MOCK_PARAMS['url'] + 'scans/1/launch',
                       json={})

    from Tenable_io import launch_scan_command

    results = launch_scan_command()
    entry_context = results['EntryContext']['TenableIO.Scan(val.Id && val.Id === obj.Id)']

    assert 'The requested scan was launched successfully' in results['HumanReadable']
    assert entry_context['Id'] == '1'


def test_get_asset_details_command(mocker, requests_mock):

    from test_data.response_and_results import MOCK_RAW_ASSET_BY_IP
    from test_data.response_and_results import MOCK_RAW_ASSET_ATTRIBUTES
    from test_data.response_and_results import EXPECTED_ASSET_INFO_RESULTS

    mock_demisto(mocker, {'ip': '1.3.2.1'})
    requests_mock.get(f"{MOCK_PARAMS['url']}workbenches/assets", json={'assets': [{'id': 'fake_asset_id'}]})
    requests_mock.get(f"{MOCK_PARAMS['url']}workbenches/assets/fake_asset_id/info",
                      json=MOCK_RAW_ASSET_BY_IP)
    requests_mock.get(f"{MOCK_PARAMS['url']}api/v3/assets/fake_asset_id/attributes",
                      json=MOCK_RAW_ASSET_ATTRIBUTES)

    from Tenable_io import get_asset_details_command

    response = get_asset_details_command()

    assert response.outputs == EXPECTED_ASSET_INFO_RESULTS
    assert response.outputs_prefix == 'TenableIO.AssetDetails'
    assert response.outputs_key_field == 'id'


@pytest.mark.parametrize('range_str, expected_lower_range_bound,expected_upper_range_bound', [
    ('2.5-3', 2.5, 3),
    ('2.5-3.5', 2.5, 3.5),
    ('0.1-3', 0.1, 3),
    ('0.1 - 3', 0.1, 3),
    ('0', 'exception', 'exception'),
    ('3-0', 'exception', 'exception')
])
def test_validate_range(range_str, expected_lower_range_bound, expected_upper_range_bound):
    """
    Given:
        - range_str (str): A string that represents a range of values in format 2.5-3.0.
    When:
        - Running the validate_range function with vprScoreRange argument.
    Then:
        - Verify that validation range function works as expected.
    """
    from Tenable_io import validate_range

    if isinstance(expected_lower_range_bound, str) and isinstance(expected_upper_range_bound, str):
        with pytest.raises(DemistoException) as de:
            lower_range_bound, upper_range_bound = validate_range(range_str)

        assert de.value.message == 'Please specify valid vprScoreRange. VPR values range are 0.1-10.0.'
    else:
        lower_range_bound, upper_range_bound = validate_range(range_str)
        assert lower_range_bound == expected_lower_range_bound
        assert upper_range_bound == expected_upper_range_bound


@freeze_time("2012-01-14", tz_offset=-4)
@pytest.mark.parametrize('date_str, expected_date', [
    ('1 day ago', 1326326400),
    ('2 days ago', 1326240000),
    ('1326232800', 1326232800)
])
def test_relational_date_to_epoch_date_format(date_str, expected_date):
    """
    Given:
        - date_str (str): A string that represents a date in epoch time or relational expression date.
    When:
        - Running the relational_date_to_epoch_date_format function.
    Then:
        - Verify date returned as epoch time as expected.
    """
    from Tenable_io import relational_date_to_epoch_date_format

    date = relational_date_to_epoch_date_format(date_str)

    assert date == expected_date


@pytest.mark.parametrize('args, expected_exception', [
    ({'vprScoreOperator': 'eq', 'vprScoreValue': '3.5', 'vprScoreRange': '3.5-3'},
     'Please specify only one of vprScoreRange or vprScoreOperator'),
    ({'vprScoreOperator': 'eq', 'vprScoreValue': '', 'vprScoreRange': ''}, 'Please specify vprScoreValue and vprScoreOperator'),
    ({'vprScoreOperator': '', 'vprScoreValue': '3.5', 'vprScoreRange': ''}, 'Please specify vprScoreValue and vprScoreOperator'),
])
def test_build_vpr_score_validation(args, expected_exception):
    """
    Given:
        - args (dict): args with vprScoreOperator,vprScoreValue and vprScoreRange.
    When:
        - Running the build_vpr_score_validation with vprScoreOperator,vprScoreValue and vprScoreRange arguments.
    Then:
        - Verify that validation function works as expected.
    """
    from Tenable_io import build_vpr_score
    with pytest.raises(DemistoException) as de:
        build_vpr_score(args)

    assert de.value.message == expected_exception


@pytest.mark.parametrize('args, expected_vpr_score', [
    ({'vprScoreOperator': 'equal', 'vprScoreValue': '3.5'}, {'eq': [3.5], 'neq': None, 'gt': None,
                                                             'lt': None, 'gte': None, 'lte': None}),
    ({'vprScoreOperator': 'not equal', 'vprScoreValue': '3.5'}, {'eq': None, 'neq': [3.5], 'gt': None,
                                                                 'lt': None, 'gte': None, 'lte': None}),
    ({'vprScoreOperator': 'lt', 'vprScoreValue': '3.5'}, {'eq': None, 'neq': None, 'gt': None,
                                                          'lt': 3.5, 'gte': None, 'lte': None}),
    ({'vprScoreOperator': 'lte', 'vprScoreValue': '3.5'}, {'eq': None, 'neq': None, 'gt': None,
                                                           'lt': None, 'gte': None, 'lte': 3.5}),
    ({'vprScoreOperator': 'gt', 'vprScoreValue': '3.5'}, {'eq': None, 'neq': None, 'gt': 3.5,
                                                          'lt': None, 'gte': None, 'lte': None}),
    ({'vprScoreOperator': 'gte', 'vprScoreValue': '3.5'}, {'eq': None, 'neq': None, 'gt': None,
                                                           'lt': None, 'gte': 3.5, 'lte': None}),
    ({'vprScoreRange': '2 - 3.3'}, {'gte': 2.0, 'lte': 3.3}),
])
def test_build_vpr_score(args, expected_vpr_score):
    """
    Given:
        - args (dict): args with vprScoreOperator,vprScoreValue and vprScoreRange.
    When:
        - Running the build_vpr_score function with vprScoreOperator,vprScoreValue and vprScoreRange arguments.
    Then:
        - Verify that build_vpr_score function works as expected.
    """
    from Tenable_io import build_vpr_score
    vpr_score = build_vpr_score(args)

    assert vpr_score == expected_vpr_score


def test_export_assets_build_command_result():
    """
    Given:
        - export_assets_response (list[dict]): An API response from Tenable.io.
    When:
        - Running the export_assets_build_command_result function.
    Then:
        - Verify command result values as expected.
    """
    from test_data.response_and_results import export_assets_response
    from Tenable_io import export_assets_build_command_result
    command_result = export_assets_build_command_result(export_assets_response)

    assert command_result.outputs == export_assets_response
    assert command_result.readable_output == '### Assets\n|ASSET ID|DNS NAME (FQDN)|SYSTEM TYPE|OPERATING SYSTEM|IPV4 ADDRESS|' \
                                             'NETWORK|FIRST SEEN|LAST SEEN|LAST LICENSED SCAN|SOURCE|TAGS|\n|' \
                                             '---|---|---|---|---|---|---|---|---|---|---|\n|' \
                                             ' XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX |' \
                                             ' some_fqdns | general-purpose | Linux Kernel 2.6 |' \
                                             ' 00.000.00.00 | Default | 2024-08-13T15:11:08.145Z ' \
                                             '| 2024-08-13T15:11:08.145Z | 2022-12-28T17:10:47.756Z |' \
                                             ' SOME_SCAN | some_key:test |\n'
    assert command_result.raw_response == export_assets_response


def test_export_vulnerabilities_build_command_result():
    """
    Given:
        - export_vulnerabilities_response (list[dict]): An API response from Tenable.io.
    When:
        - Running the export_vulnerabilities_build_command_result function.
    Then:
        - Verify command result values as expected.
    """
    from test_data.response_and_results import export_vulnerabilities_response
    from Tenable_io import export_vulnerabilities_build_command_result
    command_result = export_vulnerabilities_build_command_result(export_vulnerabilities_response)

    assert command_result.outputs == export_vulnerabilities_response
    assert command_result.readable_output == '### Vulnerabilities' \
                                             '\n|ASSET ID|ASSET NAME|IPV4 ADDRESS|OPERATING SYSTEM|SYSTEM TYPE|DNS NAME (FQDN)|' \
                                             'SEVERITY|PLUGIN ID|PLUGIN NAME|VULNERABILITY PRIORITY RATING|PROTOCOL|' \
                                             'PORT|FIRST SEEN|' \
                                             'LAST SEEN|DESCRIPTION|SOLUTION|\n|' \
                                             '---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n|' \
                                             ' XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX | some_hostname | 00.000.00.00 |' \
                                             ' Linux Kernel 2.6 | general-purpose | some_fqdn | info | 11111 | some_name |' \
                                             ' 5.2 | TCP | 21 | 2023-08-15T15:56:18.852Z | 2023-08-15T15:56:18.852Z |' \
                                             ' some_description | solution. |\n'
    assert command_result.raw_response == export_vulnerabilities_response


@pytest.mark.parametrize('args, return_value_export_request_with_export_uuid', [
    ({'chunkSize': '500'}, {"uuid": 'XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX', "status": 'PROCESSING'}),
    ({'chunkSize': '500', 'exportUuid': 'XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX'},
     {"uuid": 'XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX', "status": 'FINISHED', 'chunks_available': [1]})
])
def test_export_assets_command(mocker, args, return_value_export_request_with_export_uuid):
    """
    Given:
        - args (dict): Arguments passed down by the CLI (except from exportUuid) to provide in the HTTP request.
          return_value_export_request_with_export_uuid(dict): mock response from API.
    When:
        - Running the tenable-io-export-assets command.
    Then:
        - Verify that tenable-io-export-assets command works as expected.
    """
    from Tenable_io import export_assets_command
    import Tenable_io
    from test_data.response_and_results import export_assets_response
    mocker.patch.object(ScheduledCommand, 'raise_error_if_not_supported', return_value=None)
    mocker.patch.object(Tenable_io, 'export_request', return_value={"export_uuid": 'XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX'})
    mocker.patch.object(Tenable_io, 'export_request_with_export_uuid',
                        return_value={"export_uuid": 'XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX'})
    mocker.patch.object(Tenable_io, 'export_request_with_export_uuid',
                        return_value=return_value_export_request_with_export_uuid)
    mocker.patch.object(Tenable_io, 'get_chunks_request',
                        return_value=export_assets_response)
    mocker.patch.object(demisto, 'args',
                        return_value=args)
    response = export_assets_command(args)
    if not args.get('exportUuid'):
        assert response.readable_output == 'Waiting for export assets to finish...'
    else:
        assert response.outputs == export_assets_response
        assert response.readable_output == '### Assets\n|ASSET ID|DNS NAME (FQDN)|SYSTEM TYPE|OPERATING SYSTEM|IPV4 ADDRESS' \
                                           '|NETWORK|FIRST SEEN|LAST SEEN|LAST LICENSED SCAN|SOURCE|TAGS|\n|' \
                                           '---|---|---|---|---|---|---|---|---|---|---|\n|' \
                                           ' XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX | some_fqdns | general-purpose |' \
                                           ' Linux Kernel 2.6 | 00.000.00.00 | Default | 2024-08-13T15:11:08.145Z |' \
                                           ' 2024-08-13T15:11:08.145Z | 2022-12-28T17:10:47.756Z | SOME_SCAN | some_key:test |\n'
        assert response.raw_response == export_assets_response


@pytest.mark.parametrize('args, return_value_export_request_with_export_uuid', [
    ({'numAssets': '500'}, {"uuid": 'XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX', "status": 'PROCESSING'}),
    ({'numAssets': '500', 'exportUuid': 'XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX'},
     {"uuid": 'XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX', "status": 'FINISHED', 'chunks_available': [1]})
])
def test_export_vulnerabilities_command(mocker, args, return_value_export_request_with_export_uuid):
    """
    Given:
        - args (dict): Arguments passed down by the CLI (except from exportUuid) to provide in the HTTP request.
          return_value_export_request_with_export_uuid(dict): mock response from API.
    When:
        - Running the tenable-io-export-vulnerabilities command.
    Then:
        - Verify that tenable-io-export-vulnerabilities command works as expected.
    """
    from Tenable_io import export_vulnerabilities_command
    import Tenable_io
    from test_data.response_and_results import export_vulnerabilities_response
    mocker.patch.object(ScheduledCommand, 'raise_error_if_not_supported', return_value=None)
    mocker.patch.object(Tenable_io, 'export_request', return_value={"export_uuid": 'XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX'})
    mocker.patch.object(Tenable_io, 'export_request_with_export_uuid',
                        return_value={"export_uuid": 'XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX'})
    mocker.patch.object(Tenable_io, 'export_request_with_export_uuid',
                        return_value=return_value_export_request_with_export_uuid)
    mocker.patch.object(Tenable_io, 'get_chunks_request',
                        return_value=export_vulnerabilities_response)
    mocker.patch.object(demisto, 'args',
                        return_value=args)
    response = export_vulnerabilities_command(args)
    if not args.get('exportUuid'):
        assert response.readable_output == 'Waiting for export vulnerabilities to finish...'
    else:
        assert response.outputs == export_vulnerabilities_response
        assert response.readable_output == '### Vulnerabilities' \
                                           '\n|ASSET ID|ASSET NAME|IPV4 ADDRESS|OPERATING SYSTEM|' \
                                           'SYSTEM TYPE|DNS NAME (FQDN)|SEVERITY|PLUGIN ID|PLUGIN NAME|' \
                                           'VULNERABILITY PRIORITY RATING|PROTOCOL|PORT|FIRST SEEN|LAST SEEN|' \
                                           'DESCRIPTION|SOLUTION|\n|' \
                                           '---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n|' \
                                           ' XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX | some_hostname |' \
                                           ' 00.000.00.00 | Linux Kernel 2.6 | general-purpose | some_fqdn |' \
                                           ' info | 11111 | some_name | 5.2 | TCP | 21 |' \
                                           ' 2023-08-15T15:56:18.852Z | 2023-08-15T15:56:18.852Z |' \
                                           ' some_description | solution. |\n'
        assert response.raw_response == export_vulnerabilities_response


def test_get_json(mocker):
    '''
    Given:
        - An expected and valid response from Tenable IO

    When:
        - Running the "list-scan-filters", "get-scan-history" and "export-scan" commands.

    Then:
        - Verify that the error code is acceptable and the response json is returned.
    '''
    from Tenable_io import get_json

    mock_demisto(mocker)

    response = requests.models.Response()
    response.status_code = 200
    response._content = b'{"key": "value"}'
    assert get_json(response) == {'key': 'value'}


@pytest.mark.parametrize(
    'status_code, error_message',
    (
        (400, 'Got response status code: 400 - Possible reasons:\n'),
        (404, 'Got response status code: 404 - Tenable Vulnerability Management cannot find the specified scan.'),
        (429, 'Got response status code: 429 - Too Many Requests'),
        (500, '. Full Response:\n'),
    )
)
def test_get_json_with_error_codes(mocker, status_code, error_message):
    '''
    Given:
        - A response with an unsuccessful status code from Tenable IO

    When:
        - Running the "list-scan-filters", "get-scan-history" and "export-scan" commands.

    Then:
        - Verify that the error code is caught and an explanatory error is raised.
    '''
    from Tenable_io import get_json

    mock_demisto(mocker)

    response = requests.models.Response()
    response.status_code = status_code
    with pytest.raises(DemistoException, match=error_message):
        get_json(response)


def test_get_json_decode_error(mocker):
    '''
    Given:
        - A non-json response from Tenable IO

    When:
        - Running the "list-scan-filters", "get-scan-history" and "export-scan" commands.

    Then:
        - Verify that the unsuccessful json decoding is caught and an error is raised with the response.
    '''
    from Tenable_io import get_json

    mock_demisto(mocker)

    response = requests.models.Response()
    response.status_code = 200
    response._content = b'blabla'
    with pytest.raises(DemistoException, match='Error processing request. Unexpected response from Tenable IO:\nblabla'):
        get_json(response)


def test_list_scan_filters_command(mocker):
    '''
    Given:
        -  A request to list Tenable IO scan filters.

    When:
        - Running the "list-scan-filters" command.

    Then:
        - Verify that tenable-io-list-scan-filters command works as expected.
    '''
    from Tenable_io import list_scan_filters_command

    test_data = load_json('list_scan_filters')

    response = MockResponse(test_data['response_json'])
    requests_get = mocker.patch.object(requests, 'get', return_value=response)
    mock_demisto(mocker)

    results = list_scan_filters_command()

    assert results.outputs == test_data['outputs']
    assert results.readable_output == test_data['readable_output']
    assert results.outputs_prefix == 'TenableIO.ScanFilter'
    assert results.outputs_key_field == 'name'
    requests_get.assert_called_with(
        *test_data['called_with']['args'],
        **test_data['called_with']['kwargs'])


def test_get_scan_history_command(mocker):
    '''
    Given:
        -  A request to get Tenable IO scan history.

    When:
        - Running the "get-scan-history" command.

    Then:
        - Verify that tenable-io-get-scan-history command works as expected.
    '''
    from Tenable_io import get_scan_history_command

    test_data = load_json('get_scan_history')

    response = MockResponse(test_data['response_json'])
    requests_get = mocker.patch.object(requests, 'get', return_value=response)
    mock_demisto(mocker)

    results = get_scan_history_command(test_data['args'])

    assert results.outputs == test_data['outputs']
    assert results.readable_output == test_data['readable_output']
    assert results.outputs_prefix == 'TenableIO.ScanHistory'
    assert results.outputs_key_field == 'id'
    requests_get.assert_called_with(
        *test_data['called_with']['args'],
        **test_data['called_with']['kwargs'])


def test_initiate_export_scan(mocker):
    '''
    Given:
        - A request to export a scan report.

    When:
        - Running the "export-scan" command.

    Then:
        - Initiate an export scan request.
    '''

    from Tenable_io import initiate_export_scan

    test_data = load_json('initiate_export_scan')
    mock_demisto(mocker)
    requests_post = mocker.patch.object(
        requests, 'post', return_value=MockResponse(test_data['response_json']))
    file = initiate_export_scan(test_data['args'])

    assert file == test_data['expected_file']
    requests_post.assert_called_with(**test_data['call_args'])


def test_check_export_scan_status(mocker):
    '''
    Given:
        - A request to export a scan report.

    When:
        - Running the "export-scan" command.

    Then:
        - Initiate an export scan request.
    '''
    from Tenable_io import check_export_scan_status, HEADERS

    mock_demisto(mocker)
    requests_get = mocker.patch.object(
        requests, 'get', return_value=MockResponse({'status': 'ready'}))

    file = check_export_scan_status('scan_id', 'file_id')

    assert file == 'ready'
    requests_get.assert_called_with(
        'http://123-fake-api.com/scans/scan_id/export/file_id/status',
        headers=HEADERS, verify=False)


def test_download_export_scan(mocker):
    '''
    Given:
        - A request to export a scan report.

    When:
        - Running the "export-scan" command.

    Then:
        - Initiate an export scan request.
    '''
    from Tenable_io import download_export_scan, HEADERS

    mock_demisto(mocker)
    requests_get = mocker.patch.object(
        requests, 'get', return_value=MockResponse({}, content='content'))

    result = download_export_scan('scan_id', 'file_id', {'format': 'HTML'})

    assert result == {
        'Contents': '',
        'ContentsFormat': 'text',
        'Type': 9,
        'File': 'scan_scan_id_file_id.html',
        'FileID': 'file',
    }
    requests_get.assert_called_with(
        'http://123-fake-api.com/scans/scan_id/export/file_id/download',
        headers=HEADERS, verify=False)


@pytest.mark.parametrize(
    'args, get_response_json, post_response_json, message',
    [
        ({'scanId': '', 'format': 'HTML'}, {}, {}, 'The "chapters" field must be provided for PDF or HTML formats.'),
        ({'scanId': '', 'format': ''}, {'status': 'ready'}, {}, 'Unexpected response from Tenable IO: {}'),
        ({'scanId': '', 'format': ''}, {'status': 'error'}, {'file': 'file_id'},
         'Tenable IO encountered an error while exporting the scan report file.'),
        ({'scanId': '', 'format': ''}, {'status': 'random'}, {'file': 'file_id'},
         'Got unexpected status while exporting the scan report file: \'random\'')
    ]
)
def test_export_scan_command_errors(mocker, args, get_response_json, post_response_json, message):
    '''
    Given:
        - A request to export a scan report.

    When:
        - Running the "export-scan" command in any of the following cases:
            - Case A: The "format" arg is HTML or PDF but "chapters" is not defined.
            - Case B: The "scans/{scanId}/export" endpoint returns a json without a "file" key.
            - Case C: An export scan request has been made and the report status is "error".
            - Case D: An export scan request has been made and the report status is unrecognized.

    Then:
        - Return an error.
    '''

    from Tenable_io import export_scan_command

    mock_demisto(mocker)
    mocker.patch.object(ScheduledCommand, 'raise_error_if_not_supported')
    get_response = MockResponse(get_response_json)
    post_response = MockResponse(post_response_json)
    mocker.patch.object(requests, 'get', return_value=get_response)
    mocker.patch.object(requests, 'post', return_value=post_response)

    with pytest.raises(DemistoException, match=message):
        export_scan_command(args)
