import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_game_flow(app):
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create first user
        response = await client.post(
            "/users/",
            json={"name": "Ali", "phone": "09120000001"}
        )
        assert response.status_code == 200, response.text
        user1 = response.json()
        user1_id = user1["id"]

        # Create second user
        response = await client.post(
            "/users/",
            json={"name": "Sara", "phone": "09120000002"}
        )
        assert response.status_code == 200, response.text
        user2 = response.json()
        user2_id = user2["id"]

        # Create game
        response = await client.post("/games/")
        assert response.status_code == 200, response.text
        game = response.json()
        game_id = game["game_id"]

        # User 1 joins game
        response = await client.post(
            "/games/join",
            params={"user_id": user1_id, "game_id": game_id}
        )
        assert response.status_code == 200, response.text

        # User 2 joins game
        response = await client.post(
            "/games/join",
            params={"user_id": user2_id, "game_id": game_id}
        )
        assert response.status_code == 200, response.text

        # Check game state
        response = await client.get(f"/games/{game_id}")
        assert response.status_code == 200, response.text
        game_data = response.json()

        assert game_data["id"] == game_id
        assert game_data["status"] == "active"
        assert len(game_data["players"]) == 2

