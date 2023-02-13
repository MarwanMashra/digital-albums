from app.database.mongo import Mongo, MongoSave, MongoLoad, MongoUpd, MongoRemove
from fastapi import FastAPI, Request, File, UploadFile, APIRouter, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Depends, status  # Assuming you have the FastAPI class for routing
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_login import LoginManager
from fastapi_login.exceptions import InvalidCredentialsException  # Exception class
import pprint, json, bcrypt, os
from datetime import timedelta
import asyncio

router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory="templates")
router.mount("/static", StaticFiles(directory="static"), name="static")

coll_users = "users"

SECRET = os.urandom(24).hex()
ERROR_MSG = {
    1: "User does not exist",
    2: "Incorrect password",
    3: "User already exists",
    4: "Passwords do not match",
}

manager = LoginManager(SECRET, token_url="/auth/login", use_cookie=True)
manager.cookie_name = "access-token"


@manager.user_loader
def load_user(username: str):
    account_coll = MongoLoad({"username": username})
    accounts = list(account_coll.retrieve(coll_users, limit=1))
    if accounts:
        account = accounts[0]
        account["password"] = bytes(account["password"], "utf-8")
        return account


@router.get("/test", response_class=HTMLResponse)
def loginwithCreds(request: Request):
    email = "marwan.mashra@gmail.com"
    account_coll = MongoLoad({"email": email})
    account = list(account_coll.retrieve(coll_users, limit=1))
    return templates.TemplateResponse(
        "test.html", {"request": request, "data": account[0]}
    )


@router.get("/login", response_class=HTMLResponse, name="login_page")
def login_page(
    request: Request,
    error=None,
):
    if error:
        return templates.TemplateResponse(
            "login.html", {"request": request, "error": ERROR_MSG[int(error)]}
        )
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/auth/login", response_class=RedirectResponse)
def login(request: Request, data: OAuth2PasswordRequestForm = Depends()):
    username = data.username.lower()
    password = data.password
    user = load_user(username)
    if not user:
        error = 1
        url = request.url_for("login_page") + f"?error={error}"
        return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)
    elif bcrypt.hashpw(password.encode("utf-8"), user["password"]) != user["password"]:
        error = 2
        url = request.url_for("login_page") + f"?error={error}"
        return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)
    url = request.url_for("home_page")
    access_token = manager.create_access_token(
        data={"sub": username}, expires=timedelta(hours=12)
    )
    resp = RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)
    manager.set_cookie(resp, access_token)
    return resp


@router.get("/register", response_class=HTMLResponse, name="register_page")
def register_page(
    request: Request,
    error=None,
):
    if error:
        return templates.TemplateResponse(
            "register.html", {"request": request, "error": ERROR_MSG[int(error)]}
        )
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/auth/register", response_class=RedirectResponse)
def register(
    request: Request,
    data: OAuth2PasswordRequestForm = Depends(),
    password2: str = Form(...),
):
    username = data.username.lower()
    password = data.password
    print(username, password, password2)
    user = load_user(username)
    if user:  # user already exists
        error = 3
        url = request.url_for("register_page") + f"?error={error}"
    elif password != password2:
        error = 4
        url = request.url_for("register_page") + f"?error={error}"
    else:
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        hashed_password = str(hashed_password)[2:-1]  # convert bytes to string
        account = {"username": username, "password": hashed_password}
        documents = MongoSave([account])
        documents.storeindb(coll_users)
        url = request.url_for("login")
    resp = RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)
    return resp


@router.get("/auth", response_class=HTMLResponse)
async def home(request: Request):
    data = {"page": "auth"}
    return templates.TemplateResponse("auth.html", {"request": request, "data": data})


# @router.route('/deconnexion')
# def deconnexion():
# 	session.clear()
# 	return "success"


# @router.route('/get_session',methods=['GET'])
# def get_session():
# 	dic={}
# 	if session:
# 		dic={ 'identifiant':session['identifiant'] }
# 	return dic

""""
@mdb.route("/getQuestionnaireById", methods=["GET"])
def getQuestionnaireById():
    id = int(request.args.get("id"))
    currentTime = int(request.args.get("currentTime"))
    time_out = 0
    while True:
        db_load = MongoLoad({"id": id})
        questionnaire = list(db_load.retrieve(coll_questionnaires, limit=1))
        time_out += 1
        if questionnaire:

            db_update = MongoUpd({"id": id}, {"$set": {"last_open": currentTime}})
            db_update.singleval_upd(coll_questionnaires)

            db_load = MongoLoad({"id": id})
            questionnaire = list(db_load.retrieve(coll_questionnaires, limit=1))[0]
            break

        elif time_out > 1000:
            return None

    return questionnaire


@mdb.route("/getQuestionnaireRecent", methods=["GET"])
def getQuestionnaireRecent():
    limit = int(request.args.get("limit"))
    db_load = MongoLoad({})
    questionnaire = list(db_load.retrieve(coll_questionnaires, limit=1000000))
    list_result = []
    for x in range(0, limit):
        lastQ = None
        max = 0
        for q in questionnaire:
            if q not in list_result and q["last_open"] > max:
                lastQ = q
                max = q["last_open"]
        if lastQ != None:
            list_result.append(lastQ)

    return {"data": list_result}


@mdb.route("/getQuestionnaireByPeriod", methods=["GET"])
def getQuestionnaireByPeriod():
    period = int(request.args.get("period"))
    db_load = MongoLoad({})
    questionnaire = list(db_load.retrieve(coll_questionnaires, limit=100))
    list_result = []
    for q in questionnaire:
        if q["id"] >= period:
            list_result.append(q)

    return {"data": list_result}


@mdb.route("/getQuestionnaireByDate", methods=["GET"])
def getQuestionnaireByDate():
    startDate = int(request.args.get("startDate"))
    endDate = int(request.args.get("endDate"))
    db_load = MongoLoad({})
    questionnaire = list(db_load.retrieve(coll_questionnaires, limit=100))
    list_result = []
    for q in questionnaire:
        if q["id"] >= startDate and q["id"] <= endDate:
            list_result.append(q)

    return {"data": list_result}


@mdb.route("/getAllQuestionnaire", methods=["GET"])
def getAllQuestionnaire():
    db_load = MongoLoad({})
    questionnaire = list(db_load.retrieve(coll_questionnaires, limit=100))

    return {"data": questionnaire}


@mdb.route("/uploadQuestionnaire", methods=["POST"])
def uploadQuestionnaire():
    data = json.loads(request.data.decode("utf-8"))
    questionnaire = data["questionnaire"]
    questionnaire["last_open"] = questionnaire["id"]
    db_save = MongoSave([questionnaire])
    db_save.storeindb(coll_questionnaires)

    return "succes"


@mdb.route("/getResults", methods=["GET"])
def getResults():
    id = int(request.args.get("id"))
    db_load = MongoLoad({"id": id}, {"results": 1})
    result = list(db_load.retrieve(coll_questionnaires, limit=1))[0]["results"]
    return result


@mdb.route("/sendResults", methods=["POST"])
def sendResults():
    data = json.loads(request.data.decode("utf-8"))
    list_question_answer = data["list_question_answer"]
    color = data["color"]
    id = data["id"]
    dico = {}
    for question_answer in list_question_answer:
        field = "results." + question_answer[0] + "." + question_answer[1] + "." + color
        dico[field] = 1
        field = "results." + question_answer[0] + "." + question_answer[1] + ".total"
        dico[field] = 1

    db_update = MongoUpd({"id": id}, {"$inc": dico})
    db_update.singleval_upd(coll_questionnaires)

    return "succes"


@mdb.route("/removeQuestionnaire", methods=["POST"])
def removeQuestionnaire():
    data = json.loads(request.data.decode("utf-8"))
    id = int(data["id"])
    db_remove = MongoRemove({"id": id})
    db_remove.remove(coll_questionnaires)
    return "succes"
"""
