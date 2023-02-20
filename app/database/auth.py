from app.database.mongo import Mongo, MongoSave, MongoLoad, MongoUpd, MongoRemove
from fastapi import FastAPI, Request, File, UploadFile, APIRouter, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Depends, status  # Assuming you have the FastAPI class for routing
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_login import LoginManager
from fastapi_login.exceptions import InvalidCredentialsException  # Exception class
import bcrypt, os
from datetime import timedelta
from app.library.helpers import *


router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory="templates")
router.mount("/static", StaticFiles(directory="static"), name="static")

SECRET = os.urandom(24).hex()
ERROR_MSG = {
    1: "User does not exist",
    2: "Incorrect password",
    3: "User already exists",
    4: "Passwords do not match",
}

manager = LoginManager(SECRET, token_url="/auth/login", use_cookie=True)
manager.cookie_name = cookie_name


@manager.user_loader()
async def load_user(username: str):
    account_coll = MongoLoad({"username": username})
    account = await account_coll.retrieve(coll_users)
    if account:
        account["password"] = bytes(account["password"], "utf-8")
        return account


# async def get_username(request: Request):
#     access_token = request.cookies.get(cookie_name)
#     try:
#         user = await manager.get_current_user(access_token)
#     except:
#         print("User not logged in")
#         return None

#     return user["username"]


@router.get("/test", response_class=HTMLResponse)
async def loginwithCreds(request: Request):
    email = "marwan.mashra@gmail.com"
    account_coll = MongoLoad({"email": email})
    account = await account_coll.retrieve(coll_users)
    return templates.TemplateResponse(
        "test.html", {"request": request, "data": account}
    )


@router.get("/login", response_class=HTMLResponse, name="login_page")
def login_page(
    request: Request,
    error=None,
):
    username = get_cookie(request)
    if username:
        url = request.url_for("home_page")
        resp = RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)
        return resp
    if error:
        return templates.TemplateResponse(
            "login.html", {"request": request, "error": ERROR_MSG[int(error)]}
        )
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/auth/login", response_class=RedirectResponse)
async def login(request: Request, data: OAuth2PasswordRequestForm = Depends()):
    username = data.username.lower()
    password = data.password
    user = await load_user(username)
    if not user:
        error = 1
        url = request.url_for("login_page") + f"?error={error}"
        return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)
    elif bcrypt.hashpw(password.encode("utf-8"), user["password"]) != user["password"]:
        error = 2
        url = request.url_for("login_page") + f"?error={error}"
        return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)
    # access_token = manager.create_access_token(
    #     data={"sub": username}, expires=timedelta(hours=12)
    # )
    resp = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    # manager.set_cookie(resp, access_token)
    set_cookie(resp, username)
    return resp


@router.get("/register", response_class=HTMLResponse, name="register_page")
async def register_page(
    request: Request,
    error=None,
):
    username = get_cookie(request)
    if username:
        url = request.url_for("home_page")
        resp = RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)
        return resp
    if error:
        return templates.TemplateResponse(
            "register.html", {"request": request, "error": ERROR_MSG[int(error)]}
        )
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/auth/register", response_class=RedirectResponse)
async def register(
    request: Request,
    data: OAuth2PasswordRequestForm = Depends(),
    password2: str = Form(...),
):
    username = data.username.lower()
    password = data.password
    user = await load_user(username)
    if user:  # user already exists
        error = 3
        url = request.url_for("register_page") + f"?error={error}"
    elif password != password2:
        error = 4
        url = request.url_for("register_page") + f"?error={error}"
    else:
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        hashed_password = str(hashed_password)[2:-1]  # convert bytes to string
        account = {"username": username, "password": hashed_password, "albums": {}}
        documents = MongoSave([account])
        await documents.storeindb(coll_users)
        url = request.url_for("login_page")
    resp = RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)
    return resp


@router.get("/auth", response_class=HTMLResponse)
async def home(request: Request):
    data = {"page": "auth"}
    return templates.TemplateResponse("auth.html", {"request": request, "data": data})


@router.post("/logout", response_class=RedirectResponse)
async def logout(request: Request, response: Response):
    resp = RedirectResponse(url="/login", status_code=302)
    resp.delete_cookie(cookie_name)
    return resp
