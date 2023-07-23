import pytest
from CommonServerPython import *  # noqa # pylint: disable=unused-wildcard-import
from freezegun import freeze_time
from TrendMicroEmailSecurityEventCollector import (
    Client,
    set_first_fetch,
    # managing_set_last_run,
    fetch_by_event_type,
    fetch_events_command,
    remove_sensitive_from_events,
    NoContentException,
    EventType,
    Deduplicate,
)


@pytest.fixture()
def mock_client() -> Client:
    return Client(
        base_url="test", username="test", api_key="test", verify=False, proxy=False
    )


def load_event_for_test(test_name: str) -> list[dict]:
    return json.loads(open("test_data/test_events.json").read())[f"EVENTS_{test_name}"]


@freeze_time("2023-06-10T16:00:00Z")
@pytest.mark.parametrize(
    "start_time, expected_result",
    [("6 hours", "2023-06-10T10:00:00Z"), (None, "2023-06-10T15:00:00Z")],
)
def test_set_first_fetch(start_time: str | None, expected_result: str):
    """
    Given:
        - the time for start time or None
    When:
        - run set_first_fetch function
    Then:
        - Ensure the correct time is returned when given a start time
        - Ensure the start time is 1 hour back when no argument is given
    """
    assert set_first_fetch(start_time) == expected_result


def test_handle_error_no_content(mock_client: Client):
    """
    Given:
        - A Response object with status code 204
    When:
        - run `handle_error_no_content` method
    Then:
        - Ensure that the function throws a `NoContentException` error
    """

    class Response:
        status_code = 204

    with pytest.raises(NoContentException, match="No content"):
        mock_client.handle_error_no_content(Response())


def test_handle_error_no_content_with_other_errors(mock_client: Client):
    """
    Given:
        - A Response object with status code 404
    When:
        - run `handle_error_no_content` method
    Then:
        - Ensure the function throws an error that is not a `NoContentException`
    """

    class Response:
        status_code = 404
        reason = "test"

        def json(self):
            return {}

    with pytest.raises(DemistoException):
        mock_client.handle_error_no_content(Response())


@pytest.mark.parametrize(
    "events_key, expected_results",
    [
        ("GET_LAST_TIME_EVENT_1", "2023-07-15T10:00:20Z"),
        ("GET_LAST_TIME_EVENT_2", "2023-07-15T10:00:20Z"),
        ("GET_LAST_TIME_EVENT_3", "2023-07-15T10:00:19Z"),
    ],
)
def test_get_last_time_event(events_key: str, expected_results: str):
    """
    Given:
        - Events
    When:
        - run `get_last_time_event` method
    Then:
        - Ensure that the latest time from the list of events returns
        - Ensure the function also handles when the time format is `%Y-%m-%dT%H:%M:%S.%fZ`
    """
    dedup = Deduplicate([], EventType.ACCEPTED_TRAFFIC)
    events = load_event_for_test(events_key)
    results = dedup.get_last_time_event(events)
    assert results == expected_results


@pytest.mark.parametrize(
    "event, expected_results",
    [
        (
            {
                "subject": "test",
                "attachments": [{"fileName": "test", "sha256": "test"}],
            },
            {"attachments": [{"sha256": "test"}]},
        ),
        ({"subject": "test", "attachments": []}, {"attachments": []}),
        ({"subject": "test", "attachments": None}, {"attachments": None}),
    ],
)
def test_remove_sensitive_from_events(event: dict, expected_results: dict):
    """
    Given:
        - Events that contain `subject` or `attachments`
    When:
        - run `remove_sensitive_from_events` function
    Then:
        - Ensure that the keys with the subject or fileName values inside
          the attachments object have been deleted if those values are present in the event
    """
    remove_sensitive_from_events(event)
    assert event == expected_results


def test__encode_authorization(mock_client: Client):
    """
    Given:
        - Dummy username and dummy API key
    When:
        - run `_encode_authorization` method
    Then:
        - Ensure the username and api key are encoded and the expected value is returned
    """
    authorization_encoded = mock_client._encode_authorization("test", "test_api_key")
    assert authorization_encoded == "dGVzdDp0ZXN0X2FwaV9rZXk="


# @pytest.mark.parametrize(
#     "event_key, last_run, event_type, expected_results",
#     [
#         pytest.param(
#             "MANAGING_SET_LAST_RUN_1",
#             {},
#             EventType.ACCEPTED_TRAFFIC,
#             {
#                 f"time_{EventType.ACCEPTED_TRAFFIC.value}_from": "2023-07-14T10:00:18Z",
#                 f"fetched_event_ids_of_{EventType.ACCEPTED_TRAFFIC.value}": [
#                     "<33333.33333.33333.3333@mx.test.com>test2-test2 - 33335000"
#                 ],
#                 f"next_token_{EventType.ACCEPTED_TRAFFIC.value}": "test",
#             },
#             id="One event and last_run is empty"
#         ),
#         pytest.param(
#             "MANAGING_SET_LAST_RUN_2",
#             {},
#             EventType.ACCEPTED_TRAFFIC,
#             {
#                 f"time_{EventType.ACCEPTED_TRAFFIC.value}_from": "2023-07-15T10:00:18Z",
#                 f"fetched_event_ids_of_{EventType.ACCEPTED_TRAFFIC.value}": [
#                     "<11111.11111.11111.1111@mx.test.com>test-test2 - 11113000",
#                     "<22222.22222.22222.2222@mx.test.com>test1-test2 - 22224000",
#                 ],
#                 f"next_token_{EventType.ACCEPTED_TRAFFIC.value}": "test",
#             },
#             id="Events and last_run is empty"
#         ),
#         pytest.param(
#             "MANAGING_SET_LAST_RUN_2",
#             {
#                 f"time_{EventType.ACCEPTED_TRAFFIC.value}_from": "2023-07-12T10:00:18Z",
#                 f"fetched_event_ids_of_{EventType.ACCEPTED_TRAFFIC.value}": [
#                     "test",
#                     "test",
#                 ],
#                 f"next_token_{EventType.ACCEPTED_TRAFFIC.value}": "test0",
#             },
#             EventType.ACCEPTED_TRAFFIC,
#             {
#                 f"time_{EventType.ACCEPTED_TRAFFIC.value}_from": "2023-07-15T10:00:18Z",
#                 f"fetched_event_ids_of_{EventType.ACCEPTED_TRAFFIC.value}": [
#                     "<11111.11111.11111.1111@mx.test.com>test-test2 - 11113000",
#                     "<22222.22222.22222.2222@mx.test.com>test1-test2 - 22224000",
#                 ],
#                 f"next_token_{EventType.ACCEPTED_TRAFFIC.value}": "test",
#             },
#             id="Events with updated lust_run"
#         ),
#         pytest.param(
#             [],
#             {
#                 f"time_{EventType.ACCEPTED_TRAFFIC.value}_from": "2023-07-15T10:00:18Z",
#                 f"fetched_event_ids_of_{EventType.ACCEPTED_TRAFFIC.value}": [
#                     "<11111.11111.11111.1111@mx.test.com>test-test2 - 11113000",
#                     "<22222.22222.22222.2222@mx.test.com>test1-test2 - 22224000",
#                 ],
#                 f"next_token_{EventType.ACCEPTED_TRAFFIC.value}": "test",
#             },
#             EventType.ACCEPTED_TRAFFIC,
#             {
#                 f"time_{EventType.ACCEPTED_TRAFFIC.value}_from": "2023-07-15T10:00:18Z",
#                 f"fetched_event_ids_of_{EventType.ACCEPTED_TRAFFIC.value}": [
#                     "<11111.11111.11111.1111@mx.test.com>test-test2 - 11113000",
#                     "<22222.22222.22222.2222@mx.test.com>test1-test2 - 22224000",
#                 ],
#                 f"next_token_{EventType.ACCEPTED_TRAFFIC.value}": "test",
#             },
#             id="No events"
#         ),
#     ],
# )
# def test_managing_set_last_run(
#     event_key: str, last_run, event_type, expected_results
# ):
#     """
#     Given:
#         - The arguments needed for the `managing_set_last_run` function
#     When:
#         - run `managing_set_last_run` function
#     Then:
#         - Ensure the `last_run` object returns with `from_time`
#           that matches 'event_type' when the API call returns an event with 'genTime'
#         - Ensure the last_run update is done both when last_run is given full and
#           when it is empty when events are returned
#         - Ensure the 'last_run' is returned unchanged
#           when no events are returned from the API
#     """
#     dedup = Deduplicate([], event_type)
#     events = load_event_for_test(event_key)
#     results = managing_set_last_run(
#         events=events, last_run=last_run, start="", event_type=event_type, deduplicate=dedup,
#     )
#     assert results == expected_results


@pytest.mark.parametrize(
    "event_mock, limit",
    [(({"nextToken": "abc%20abc", "logs": [{"genTime": "test"}]}, {}), 2)],
)
def test_fetch_by_event_type_token_unquote(
    mocker, mock_client: Client, event_mock: tuple[dict], limit: int
):
    """
    Given:
        - next_token with quote character
    When:
        - run fetch_by_event_type function
    Then:
        - Ensure that the next_token argument sent to the API request is unquoted
    """
    mock_api = mocker.patch.object(mock_client, "get_logs", side_effect=event_mock)
    fetch_by_event_type(
        mock_client, "", "", limit, [], EventType.ACCEPTED_TRAFFIC, False
    )
    assert mock_api.call_args[0][1]["token"] == "abc abc"


@pytest.mark.parametrize(
    "event_mock, limit, expected_results",
    [
        pytest.param(
            ({},),
            1,
            {"len_events": 0, "call_count": 1},
            id="No logs and nextToken were returned",
        ),
        pytest.param(
            ({"nextToken": "test", "logs": [{"genTime": "test"}]}, {}),
            2,
            {"len_events": 1, "call_count": 2},
            id="No logs and nextToken were returned (second iteration)",
        ),
        pytest.param(
            ({"logs": [{"genTime": "test"}]},),
            1,
            {"len_events": 1, "call_count": 1},
            id="no nextToken returned",
        ),
        pytest.param(
            (
                {"nextToken": "test", "logs": [{"genTime": "test"}]},
                {"logs": [{"genTime": "test"}]},
            ),
            2,
            {"len_events": 2, "call_count": 2},
            id="no nextToken returned (second iteration)",
        ),
        pytest.param(
            (NoContentException(),),
            1,
            {"len_events": 0, "call_count": 1},
            id="NoContentException returned",
        ),
        pytest.param(
            (
                {"nextToken": "test", "logs": [{"genTime": "test"}]},
                NoContentException(),
            ),
            2,
            {"len_events": 1, "call_count": 2},
            id="NoContentException returned (second iteration)",
        ),
        pytest.param(
            (
                {"nextToken": "test", "logs": [{"genTime": "test"}]},
                {"nextToken": "test", "logs": [{"genTime": "test"}]},
            ),
            2,
            {"len_events": 2, "call_count": 2},
            id="len(events) == limit",
        ),
    ],
)
def test_fetch_by_event_type(
    mocker,
    mock_client: Client,
    event_mock: tuple[dict],
    limit: int,
    expected_results: dict,
):
    """
    Given:
        - args for fetch_by_event_type function
    When:
        - run fetch_by_event_type function and return from api request response by event mock
    Then:
        - Ensure that when no events are returned from the API
          it exits the while loop and returns 0 events.
        - Ensure that when in the second iteration no events are returned from the API,
          it exits the while loop and returns 1 event and the api call is called twice.
        - Ensure that when no `nextToken` returns from the API
          it exits the while loop and returns 1 event
        - Ensure that when in the second iteration `nextToken` does not return from the API
          it exits the while loop and returns 1 event and the api call is called twice.
        - Ensure that when `NoContentException` returns from the API
          it exits the while loop and returns 0 events
        - Ensure that when in the second iteration `NoContentException` returns from the API
          it exits the while loop and returns 1 event and the api call is called twice.
        - Ensure that when the number of events returned from the API is equal to the `limit`
          it exits the while loop and returns events as expected.
    """
    mock_api = mocker.patch.object(mock_client, "get_logs", side_effect=event_mock)
    events, _ = fetch_by_event_type(
        mock_client, "", "", limit, [], EventType.ACCEPTED_TRAFFIC, False
    )

    assert len(events) == expected_results["len_events"]
    assert mock_api.call_count == expected_results["call_count"]


@pytest.mark.parametrize(
    "args, first_fetch, last_run, expected_calls",
    [
        (
            {"max_fetch": 1},
            "2023-02-11T15:47:25Z",
            {},
            [
                {"limit": 1, "start": "2023-02-11T15:47:25Z"},
                {"limit": 1, "start": "2023-02-11T15:47:25Z"},
                {"limit": 1, "start": "2023-02-11T15:47:25Z"},
            ],
        ),
        (
            {
                "max_fetch": 1,
            },
            "2023-02-11T15:47:25Z",
            {
                f"time_{EventType.POLICY_LOGS.value}_from": "2023-07-11T15:47:25Z",
                f"time_{EventType.ACCEPTED_TRAFFIC.value}_from": "2023-08-11T15:47:25Z",
                f"time_{EventType.BLOCKED_TRAFFIC.value}_from": "2023-09-11T15:47:25Z",
            },
            [
                {"limit": 1, "start": "2023-08-11T15:47:25Z"},
                {"limit": 1, "start": "2023-09-11T15:47:25Z"},
                {"limit": 1, "start": "2023-07-11T15:47:25Z"},
            ],
        ),
        (
            {},
            "2023-02-11T15:47:25Z",
            {
                f"time_{EventType.ACCEPTED_TRAFFIC.value}_from": "2023-08-11T15:47:25Z",
                f"time_{EventType.BLOCKED_TRAFFIC.value}_from": "2023-09-11T15:47:25Z",
            },
            [
                {"limit": 5000, "start": "2023-08-11T15:47:25Z"},
                {"limit": 5000, "start": "2023-09-11T15:47:25Z"},
                {"limit": 5000, "start": "2023-02-11T15:47:25Z"},
            ],
        ),
    ],
)
def test_fetch_events_command(
    mocker,
    mock_client: Client,
    args: dict[str, str],
    first_fetch: str,
    last_run: dict[str, str],
    expected_calls: list,
):
    """
    Given:
        - Fetch start time and last_run object and other arguments
    When:
        - run `fetch_events_command` function
    Then:
        - Ensure the `fetch_by_event_type` function is called 3 times,
          each call with the start time and limit that match the event_type
    """
    mock_func = mocker.patch(
        "TrendMicroEmailSecurityEventCollector.fetch_by_event_type",
        return_value=([{"_time": "test", "logType": "test"}], "test"),
    )
    mocker.patch(
        "TrendMicroEmailSecurityEventCollector.managing_set_last_run", return_value={}
    )
    fetch_events_command(mock_client, args, first_fetch, last_run)

    assert mock_func.call_count == 3
    for i in range(3):
        assert mock_func.call_args_list[i][1]["limit"] == expected_calls[i]["limit"]
        assert mock_func.call_args_list[i][1]["start"] == expected_calls[i]["start"]


@pytest.mark.parametrize(
    "event_key, event_type, expected_results",
    [
        (
            "GENERATE_ID_FOR_EVENT_1",
            EventType.POLICY_LOGS,
            "<11111.11111.11111.1111@mx.test.com>",
        ),
        (
            "GENERATE_ID_FOR_EVENT_2",
            EventType.ACCEPTED_TRAFFIC,
            "test12345",
        ),
    ],
)
def test_generate_id_for_event(
    event_key: str, event_type: EventType, expected_results: str
):
    """
    Given:
        - event
    When:
        - run `generate_id_for_event` function
    Then:
        - Ensure that ID is returned which is generated
          by concatenating values included in the event
        - Ensure the function generates an ID even when
          some of the values are missing or some are equal to `None`
    """
    dedup = Deduplicate([], event_type)
    event = load_event_for_test(event_key)
    result = dedup.generate_id_for_event(event[0])
    assert result == expected_results


@pytest.mark.parametrize(
    "event_key, latest_time, expected_results",
    [
        (
            "GET_EVENT_IDS_WITH_DUPLICATION_RISK",
            "2023-07-15T10:00:18Z",
            [
                "<11111.11111.11111.1111@mx.test.com>",
                "<22222.22222.22222.2222@mx.test.com>",
            ],
        )
    ],
)
def test_get_event_ids_with_duplication_risk(
    event_key: str, latest_time: str, expected_results: list[str]
):
    """
    Given:
        - The events
    When:
        - run `get_event_ids_with_duplication_risk` function
    Then:
        - Ensure the function returned the IDs of all events that are suspected of being duplicates
    """
    dedup = Deduplicate([], EventType.POLICY_LOGS)
    events = load_event_for_test(event_key)
    results = dedup.get_event_ids_with_duplication_risk(events, latest_time)
    assert len(results) == len(expected_results)
    for result in results:
        assert result in expected_results


@pytest.mark.parametrize(
    "event_key, ids_fetched_by_type, time_from, expected_results",
    [
        (
            "DEDUPLICATE_1",
            ["<11111.11111.11111.1111@mx.test.com>"],
            "2023-07-15T10:00:18Z",
            2,
        ),
        (
            "DEDUPLICATE_2",
            [],
            "2023-07-15T10:00:18Z",
            3,
        ),
    ],
)
def test_deduplicate(
    event_key: str,
    ids_fetched_by_type: list[str],
    time_from: str,
    expected_results,
):
    """
    Given:
        - The events
    When:
        - run `is_duplicate` method
    Then:
        - Ensure that the events found with an ID that matches
          the value in the `ids_fetched_by_type` list are removed
    """
    dedup = Deduplicate(ids_fetched_by_type, EventType.POLICY_LOGS)
    events = []
    for event in load_event_for_test(event_key):
        if not dedup.is_duplicate(event, time_from):
            events.append(event)
    assert expected_results == len(events)


def test_e2e_for_fetch_process(
    mocker, mock_client: Client, mock_value, expected_results
):
    ...
