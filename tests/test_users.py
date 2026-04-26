# tests/test_users.py
from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from tests.conftest import auth_header, create_test_user, login_user


@pytest.mark.anyio  # decorator to mark async test functions
async def test_create_user_validation_error(client: AsyncClient):
    response = await client.post(
        "/api/users",
        json={
            "username": "testuser",
        },
    )

    assert response.status_code == 422
    assert "email" in response.text
    assert "password" in response.text


@pytest.mark.anyio
async def test_create_user_duplicate_email(client: AsyncClient):
    await create_test_user(client)

    response = await client.post(
        "/api/users",
        json={
            "username": "different_user",
            "email": "test@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


@pytest.mark.anyio
async def test_create_user_success(client: AsyncClient):
    response = await client.post(
        "/api/users",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepassword123",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert "id" in data
    assert "image_path" in data
    assert "password" not in data
    assert "password_hash" not in data


@pytest.mark.anyio
async def test_upload_profile_picture(client: AsyncClient, mocked_aws):
    user = await create_test_user(client)
    token = await login_user(client)

    # Patch the app's S3 client to use the mocked one
    #with patch("image_utils.boto3.client", return_value=mocked_aws):
    with patch("boto3.client", return_value=mocked_aws):
        test_image_path = Path(__file__).parent / "test_image.jpg"
        image_bytes = test_image_path.read_bytes()

        response = await client.patch(
            f"/api/users/{user['id']}/picture",
            files={"file": ("profile.jpg", BytesIO(image_bytes), "image/jpeg")},
            headers=auth_header(token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["image_file"] is not None
        assert data["image_file"].endswith(".jpg")
        # assert "s3" in data["image_path"] # failing because we're using moto, which doesn't use the same S3 endpoint URL as our app config

        s3_objects = mocked_aws.list_objects_v2(Bucket="test-bucket")
        assert "Contents" in s3_objects
        assert len(s3_objects["Contents"]) == 1
        assert s3_objects["Contents"][0]["Key"].endswith(data["image_file"])


@pytest.mark.anyio
async def test_forgot_password_sends_email(client: AsyncClient):
    await create_test_user(client)

    with patch( 
        # @patch (from unittest.mock), temporarily replace (mock) a function, class, object, or module during a test # prevent sending real emails during tests
        "routers.users.send_password_reset_email", 
        # ^ why not "email_utils.send_password_reset_email" --- 
        # reason: @patch patches the name where it is imported and used, not where the function is originally defined.
        new_callable=AsyncMock,
    ) as mock_send:
        response = await client.post(
            "/api/users/forgot-password", # endpoint that triggers the password reset email
            json={"email": "test@example.com"},
        )

        assert response.status_code == 202
        mock_send.assert_awaited_once() # checks: The mocked async function was called (awaited) exactly once, and It was called using await, not a normal synchronous call.
        call_kwargs = mock_send.call_args.kwargs
        assert call_kwargs["to_email"] == "test@example.com"
        assert call_kwargs["username"] == "testuser"
        assert "token" in call_kwargs

"""
using @patch decorator (Cleaner and more professional):

from unittest.mock import patch, AsyncMock, ANY
import pytest

@pytest.mark.anyio
@patch("routers.users.send_password_reset_email", new_callable=AsyncMock)
async def test_forgot_password_sends_reset_email(
    mock_send_email: AsyncMock, 
    client: AsyncClient
):
    #Test that forgot-password endpoint sends password reset email.
    # Arrange
    await create_test_user(client)

    # Act
    response = await client.post(
        "/api/users/forgot-password",
        json={"email": "test@example.com"}
    )

    # Assert
    assert response.status_code == 202
    
    # Verify the email sending function was called correctly
    mock_send_email.assert_awaited_once_with(
        to_email="test@example.com",
        username="testuser",
        token=ANY                     # token is random, so we don't check exact value
    )
"""

# uv run pytest tests/test_users.py -v
# uv run pytest tests/test_users.py::test_upload_profile_picture -v


"""
Why anyio instead of pytest-asyncio?
FastAPI itself is built on Starlette, which uses anyio for its asynchronous capabilities, 
anyio provides compatibility across different async backends (asyncio, trio),
The FastAPI ecosystem has standardized on anyio for testing async code
- anyio is a more modern and flexible async testing framework that supports multiple async libraries (asyncio, trio, curio) with a single API. pytest-asyncio is specific to asyncio.
- anyio provides better support for async fixtures and test parametrization, making it easier to write complex async tests. pytest-asyncio can be more limited in these areas.

asyncio: is Python's built-in asynchronous runtime that powers everything in FastAPI, but it doesn't provide testing utilities on its own. 
pytest-asyncio is a plugin that adds support for testing asyncio code, but it can be less flexible and may not work well with other async libraries.
- FastAPI's application lifecycle runs on asyncio
- Uvicorn (the ASGI server) creates and manages the asyncio event loop
- asyncpg(for postgres) operates within the asyncio event loop
When we use @pytest.mark.anyio, it runs your test functions on asyncio backend by default.
"""