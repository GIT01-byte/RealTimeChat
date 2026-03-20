import httpx
from fastapi import HTTPException, Request, status

from .schemas import UserData


async def get_current_user(request: Request):
    async with httpx.AsyncClient() as client:
        try:
            auth_token = request.headers.get("authorization")
            print(f"INFO:    get_current_user получил - {auth_token}")

            if auth_token:
                auth_header = {"Authorization": f"{auth_token}"}

                login_response = await client.get(
                    "http://krakend:8080/user/self_info/",
                    headers=auth_header,
                    follow_redirects=True,
                )
            else:
                print("EXC:   get_current_user    Get cookie fail")
                raise HTTPException(status_code=500, detail="Get cookie fail")

            if login_response.status_code != 200:
                print(
                    f"EXC:   get_current_user    Authorization failed: {login_response.text}"
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Authorization failed: {login_response.text}",
                )

            response_data: dict = login_response.json()
            print(f"INFO:    get_current_user обработал - {response_data}")

            return UserData(
                user_id=response_data["user_db"]["id"],
                username=response_data["user_db"]["username"],
                email=response_data["user_db"]["email"],
                is_active=response_data["user_db"]["is_active"],
                jti=response_data["jwt_payload"]["jti"],
                access_expire=response_data["jwt_payload"]["exp"],
                iat=response_data["jwt_payload"]["iat"],
            )

        except httpx.RequestError as exc:
            print(f"EXC:   get_current_user    Gateway unavailable: {exc}")
            raise HTTPException(status_code=503, detail=f"Gateway unavailable: {exc}")
