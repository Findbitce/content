import pytest

from IAMApiModule import *
from Salesforce_IAM import Client, IAMUserProfile, get_user_command, create_user_command, \
    update_user_command, handle_exception


def mock_client():
    client = Client(
        demisto_params={},
        base_url='base_url',
        conn_client_id="client_id",
        conn_client_secret="client_secret",
        conn_username="",
        conn_password="password",
        ok_codes=(200, 201, 204),
        verify=True,
        proxy=True
    )

    return client


create_inp_schme = {
    "username": "test@palo.com",
    "Email": "test@palo.com",
    "LastName": "haim",
    "FirstName": "test",
    "Alias": "a",
    "TimeZoneSidKey": "Asia/Tokyo",
    "LocaleSidKey": "en_US",
    "EmailEncodingKey": "ISO-8859-1",
    "ProfileId": "00e4K000001GgCL",
    "LanguageLocaleKey": "en_US"
}

demisto.callingContext = {'context': {'IntegrationInstance': 'Test', 'IntegrationBrand': 'Test'}}

SALESFORCE_GET_USER_OUTPUT = {
    "Email": "TestID@networks.com",
    "Username": "TestID@networks.com",
    "FirstName": "test",
    "Id": "12345",
    "IsActive": True
}


SALESFORCE_CREATE_USER_OUTPUT = {
    "id": "12345"
}


def get_outputs_from_user_profile(user_profile):
    entry_context = user_profile.to_entry()
    outputs = entry_context.get('Contents')

    return outputs


def test_create_user_command(mocker):
    args = {"user-profile": {"email": "mock@mock.com"}}
    mocker.patch.object(Client, 'get_access_token_', return_value='')
    client = mock_client()

    mocker.patch.object(IAMUserProfile, 'map_object', return_value={"Email": "mock@mock.com"})
    mocker.patch.object(client, 'create_user', return_value=SALESFORCE_CREATE_USER_OUTPUT)
    mocker.patch.object(client, 'get_user_id_and_activity', return_value=(None, None))

    iam_user_profile = create_user_command(client, args, 'mapper_out', True, True, True)
    outputs = get_outputs_from_user_profile(iam_user_profile)

    assert outputs.get('action') == IAMActions.CREATE_USER
    assert outputs.get('success') is True
    assert outputs.get('active') is True
    assert outputs.get('id') == '12345'


def test_get_user_command__existing_user(mocker):
    args = {"user-profile": {"email": "mock@mock.com"}}
    mocker.patch.object(Client, 'get_access_token_', return_value='')
    client = mock_client()

    mocker.patch.object(client, 'get_user', return_value=SALESFORCE_GET_USER_OUTPUT)
    mocker.patch.object(client, 'get_user_id_and_activity', return_value=("id", None))
    mocker.patch.object(IAMUserProfile, 'update_with_app_data', return_value={})
    mocker.patch.object(demisto, 'mapObject', return_value={"Email": "mock@mock.com"})

    iam_user_profile = get_user_command(client, args, 'mapper_in', 'mapper_out')
    outputs = get_outputs_from_user_profile(iam_user_profile)

    assert outputs.get('action') == IAMActions.GET_USER
    assert outputs.get('success') is True
    assert outputs.get('active') is True
    assert outputs.get('id') == '12345'
    assert outputs.get('username') == 'TestID@networks.com'


def test_get_user_command__non_existing_user(mocker):
    args = {"user-profile": {"email": "mock@mock.com"}}
    mocker.patch.object(Client, 'get_access_token_', return_value='')
    client = mock_client()

    mocker.patch.object(client, 'get_user_id_and_activity', return_value=(None, None))
    mocker.patch.object(client, 'get_user', return_value={})
    mocker.patch.object(demisto, 'mapObject', return_value={"Email": "mock@mock.com"})

    iam_user_profile = get_user_command(client, args, 'mapper_in', 'mapper_out')
    outputs = get_outputs_from_user_profile(iam_user_profile)

    assert outputs.get('action') == IAMActions.GET_USER
    assert outputs.get('success') is False
    assert outputs.get('errorCode') == IAMErrors.USER_DOES_NOT_EXIST[0]
    assert outputs.get('errorMessage') == IAMErrors.USER_DOES_NOT_EXIST[1]


def test_create_user_command__user_already_exists(mocker):
    args = {"user-profile": {"email": "mock@mock.com"}}
    mocker.patch.object(Client, 'get_access_token_', return_value='')
    client = mock_client()

    mocker.patch.object(client, 'get_user_id_and_activity', return_value=("mock@mock.com", ""))
    mocker.patch.object(client, 'get_user', return_value={"email": "mock@mock.com"})
    mocker.patch.object(client, 'update_user', return_value={})
    mocker.patch.object(demisto, 'mapObject', return_value={"Email": "mock@mock.com"})

    iam_user_profile = create_user_command(client, args, 'mapper_out', True, True, True)
    outputs = get_outputs_from_user_profile(iam_user_profile)

    assert outputs.get('action') == IAMActions.UPDATE_USER
    assert outputs.get('success') is True


def test_update_user_command__non_existing_user(mocker):
    args = {"user-profile": {"email": "mock@mock.com"}}
    mocker.patch.object(Client, 'get_access_token_', return_value='')
    client = mock_client()

    mocker.patch.object(client, 'get_user_id_and_activity', return_value=(None, None))
    mocker.patch.object(demisto, 'mapObject', return_value={"Email": "mock@mock.com"})
    mocker.patch.object(client, 'create_user', return_value=SALESFORCE_CREATE_USER_OUTPUT)

    iam_user_profile = update_user_command(client, args, 'mapper_out', is_command_enabled=True, is_enable_enabled=True,
                                           is_create_user_enabled=True, create_if_not_exists=True)
    outputs = get_outputs_from_user_profile(iam_user_profile)

    assert outputs.get('action') == IAMActions.CREATE_USER
    assert outputs.get('success') is True
    assert outputs.get('active') is True
    assert outputs.get('id') == '12345'


def test_update_user_command__command_is_disabled(mocker):
    args = {"user-profile": {"email": "mock@mock.com"}}
    mocker.patch.object(Client, 'get_access_token_', return_value='')
    client = mock_client()

    mocker.patch.object(client, 'get_user_id_and_activity', return_value=(None, None))
    mocker.patch.object(IAMUserProfile, 'map_object', return_value={})
    mocker.patch.object(client, 'update_user')

    user_profile = update_user_command(client, args, 'mapper_out', is_command_enabled=False, is_enable_enabled=False,
                                       is_create_user_enabled=False, create_if_not_exists=False)
    outputs = get_outputs_from_user_profile(user_profile)

    assert outputs.get('action') == IAMActions.UPDATE_USER
    assert outputs.get('success') is True
    assert outputs.get('skipped') is True
    assert outputs.get('reason') == 'Command is disabled.'


class MockResponse:
    def __init__(self, res):
        self.status_code = 400
        self.text = res

    def json(self):
        return json.loads(self.text)


@pytest.mark.parametrize(
    'e, is_crud_command, expected_error_code, expected_error_message',
    [
        (
            DemistoException('', res=MockResponse('[{"errorCode": 400, "message": "message"}]')),
            True, 400, '[{"errorCode": 400, "message": "message"}]'
        ),
        (
            DemistoException('', res=MockResponse('[{"errorCode": 400, "message": "message"}]')),
            False, 400, 'message'
        ),
        (
            DemistoException('', res=MockResponse('text_message')),
            False, '', 'text_message'
        ),
        (
            ValueError('ValueError message'),
            False, '', 'ValueError message'
        ),
    ]
)
def test_handle_exception(mocker, e, is_crud_command, expected_error_code, expected_error_message):
    mocker.patch.object(demisto, 'error', return_value=None)  # avoid printing to stdout
    error_message, error_code = handle_exception(e, is_crud_command=is_crud_command)

    assert error_code == expected_error_code
    assert error_message == expected_error_message
