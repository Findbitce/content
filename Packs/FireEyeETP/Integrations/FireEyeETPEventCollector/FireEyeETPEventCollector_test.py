from datetime import datetime, timezone
import json
import pytest
import FireEyeETPEventCollector
from freezegun import freeze_time


def util_load_json(path):
    with open(path, encoding='utf-8') as f:
        return json.loads(f.read())


#  ########### FORMAT RESULTS TEST ################


EVENT_CASES = [
    (
        FireEyeETPEventCollector.EventType('alerts', 20, 200, outbound=False),  # event config
        True,  # hidden param
        'test_data/alerts.json',  # path to mocked data
        "formatted_response_hidden_true"  # name of expected response key
    ),
    (
        FireEyeETPEventCollector.EventType('alerts', 20, 200, outbound=False),  # event config
        False,  # hidden param
        'test_data/alerts.json',  # path to mocked data
        "formatted_response_hidden_false"  # name of expected response key
    ),
    (
        FireEyeETPEventCollector.EventType('alerts', 20, 200, outbound=True),
        True,  # hidden param
        'test_data/alerts.json',
        "formatted_response_hidden_true"  # name of expected response key
    ),
    (
        FireEyeETPEventCollector.EventType('alerts', 20, 200, outbound=True),
        False,  # hidden param
        'test_data/alerts.json',
        "formatted_response_hidden_false"  # name of expected response key
    ),
    (
        FireEyeETPEventCollector.EventType('activity_log', 20, 200, outbound=False),
        True,  # hidden param
        'test_data/activity_log.json',
        "formatted_response"
    ),
    (
        FireEyeETPEventCollector.EventType('activity_log', 20, 200, outbound=True),
        True,  # hidden param
        'test_data/activity_log.json',
        "formatted_response"
    ),
    (
        FireEyeETPEventCollector.EventType('email_trace', 20, 200, outbound=False),
        True,  # hidden param
        'test_data/activity_log.json',
        "formatted_response_hidden_true"
    ),
    (
        FireEyeETPEventCollector.EventType('email_trace', 20, 200, outbound=True),
        True,  # hidden param
        'test_data/activity_log.json',
        "formatted_response_hidden_true"
    ),
    (
        FireEyeETPEventCollector.EventType('email_trace', 20, 200, outbound=False),
        False,  # hidden param
        'test_data/activity_log.json',
        "formatted_response_hidden_false"
    ),
    (
        FireEyeETPEventCollector.EventType('email_trace', 20, 200, outbound=True),
        False,  # hidden param
        'test_data/activity_log.json',
        "formatted_response_hidden_false"
    ),

]

LAST_RUN_MULTIPLE_EVENT = {'Last Run': {
    "alerts": {
        "last_fetch_last_ids": ['a', 'b'],
        'last_fetch_timestamp': '2023-07-19T12:37:00.028000'
    },
    "email_trace": {
        "last_fetch_last_ids": [],
        'last_fetch_timestamp': '2023-07-19T12:20:00.020000'
    },
    "activity_log": {
        "last_fetch_last_ids": [],
        'last_fetch_timestamp': '2023-07-19T12:20:00.020000'
    }

}}
LAST_RUN_ONE_EVENT = {'Last Run': {
    "alerts": {
        "last_fetch_last_ids": ['a', 'b'],
        'last_fetch_timestamp': '2023-07-19T12:37:00.028000'
    },
}}

LAST_RUN_EMPTY = {}
LAST_RUN_DICT_CASES = [
    (LAST_RUN_MULTIPLE_EVENT,
     [
         FireEyeETPEventCollector.EventType('alerts', 25, outbound=False),
         FireEyeETPEventCollector.EventType('email_trace', 25, outbound=False),
         FireEyeETPEventCollector.EventType('activity_log', 25, outbound=False),
     ],
     LAST_RUN_MULTIPLE_EVENT),
    (LAST_RUN_ONE_EVENT,
     [FireEyeETPEventCollector.EventType('alerts', 25, outbound=False)],
     LAST_RUN_ONE_EVENT)

]


@ pytest.mark.parametrize('last_run_dict, event_types_to_run, expected', LAST_RUN_DICT_CASES)
def test_last_run(last_run_dict, event_types_to_run, expected):
    """
        Given: mocked last run dictionary and events to fetch
        When: trying to fetch events
        Then: validate last run creation and save.
    """
    last_run = FireEyeETPEventCollector.get_last_run_from_dict(last_run_dict, event_types_to_run)
    assert len(last_run.event_types) == len(expected.get('Last Run', {}))
    assert {e.name for e in event_types_to_run} - set(last_run.__dict__.keys()) == set()
    new_dict = last_run.to_demisto_last_run()
    assert new_dict['Last Run'].keys() == expected['Last Run'].keys()


def mock_client():
    return FireEyeETPEventCollector.Client(
        base_url='https://test.com',
        verify_certificate=False,
        proxy=False,
        api_key='api-key',
        outbound_traffic=False,
        hide_sensitive=True
    )


@ freeze_time("2023-07-18 11:34:30")
def test_fetch_alerts(mocker):
    """
    Given: mocked client, mocked responses and expected event structure,
    When: fetching incidents
    Then: Testing the formatted events are as required.
    """
    # Test case 1: Check if the alerts fetch
    mocked_alert_data = util_load_json('test_data/alerts.json')
    mocked_trace_data = util_load_json('test_data/email_trace.json')
    mocked_activity_data = util_load_json('test_data/activity_log.json')
    event_types_to_run = [
        FireEyeETPEventCollector.EventType('alerts', 25, outbound=False),
        FireEyeETPEventCollector.EventType('email_trace', 1000, outbound=False),
        FireEyeETPEventCollector.EventType('activity_log', 25, outbound=False)
    ]
    collector = FireEyeETPEventCollector.EventCollector(mock_client(), event_types_to_run)
    mocker.patch.object(FireEyeETPEventCollector.Client, 'get_alerts', side_effect=[
                        mocked_alert_data['ok_response_single_data'], {'data': []}])
    mocker.patch.object(FireEyeETPEventCollector.Client, 'get_email_trace', side_effect=[
                        mocked_trace_data['ok_response_single_data'], {'data': []}])
    mocker.patch.object(FireEyeETPEventCollector.Client, 'get_activity_log', side_effect=[
                        mocked_activity_data['ok_response'], {'data': []}])
    next_run, events = collector.fetch_command(
        demisto_last_run=LAST_RUN_MULTIPLE_EVENT,
        first_fetch=datetime.now(),
        max_fetch=1,
    )
    assert events[0] == mocked_alert_data['formatted_response_hidden_true']
    assert events[1] == mocked_trace_data['formatted_response_hidden_true']
    assert events[2] == mocked_activity_data['formatted_response']


FAKE_ISO_DATE_CASES = [
    ("2023-08-01T14:15:26.123456+0000Z", datetime(2023, 8, 1, 14, 15, 26, 123456, tzinfo=timezone.utc)),
    ("2023-08-01T14:15:26+0000Z", datetime(2023, 8, 1, 14, 15, 26, tzinfo=timezone.utc)),
    ("2023-08-01T14:15:26+0000", datetime(2023, 8, 1, 14, 15, 26, tzinfo=timezone.utc)),
    ("2023-08-01 14:15:26+0000Z", None),  # Invalid format, expecting ValueError
    ("2023-08-01T14:15:26Z", datetime(2023, 8, 1, 14, 15, 26, tzinfo=timezone.utc)),
]


@pytest.mark.parametrize("input_str, expected_dt", FAKE_ISO_DATE_CASES)
def test_from_fake_isozformat(input_str, expected_dt):
    """
    Given: date string in differents formats
    When: trying to convert from response to datetime
    Then: make sure parsing is correct.
    """
    if expected_dt is None:
        with pytest.raises(ValueError):
            FireEyeETPEventCollector.from_fake_isozformat(input_str)
    else:
        assert FireEyeETPEventCollector.from_fake_isozformat(input_str) == expected_dt


class TestLastRun:
    @pytest.fixture
    def last_run(self):
        """
            Given: events
            When: trying to create last run
            Then: make sure last run created with the events.
        """
        # Create a LastRun instance with dummy event types
        event_types = [FireEyeETPEventCollector.EventType('alerts', 25, outbound=False),
                       FireEyeETPEventCollector.EventType('email_trace', 25, outbound=False),
                       FireEyeETPEventCollector.EventType('activity_log', 25, outbound=False)
                       ]
        return FireEyeETPEventCollector.LastRun(event_types=event_types)

    def test_to_demisto_last_run_empty(self, last_run):
        # Test to_demisto_last_run method when there are no event types
        last_run.event_types = []
        assert last_run.to_demisto_last_run() == {}
