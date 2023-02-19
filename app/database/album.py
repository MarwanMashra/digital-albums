from app.database.mongo import Mongo, MongoSave, MongoLoad, MongoUpd, MongoRemove
from fastapi import FastAPI, Request, File, UploadFile, APIRouter, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Depends, status  # Assuming you have the FastAPI class for routing
from fastapi_login.exceptions import InvalidCredentialsException  # Exception class
from app.database.auth import get_username
from app.library.helpers import *
import uuid


router = APIRouter(tags=["album"])
templates = Jinja2Templates(directory="templates")
router.mount("/static", StaticFiles(directory="static"), name="static")


@router.post("/get_albums")
async def get_albums(request: Request):
    username = await get_username(request)
    account_coll = MongoLoad({"username": username})
    account = await list(account_coll.retrieve(coll_users, limit=1))[0]
    return account["albums"]


@router.get("/album/{album_id}", name="album_page", response_class=HTMLResponse)
def album(request: Request, album_id: str):
    return templates.TemplateResponse(
        "album.html", {"request": request, "album_name": album_id}
    )


@router.post("/album/{album_id}")
async def album(request: Request, album_id: str):
    if album_id[0] == "v":
        url_type = "view_url"
    elif album_id[0] == "e":
        url_type = "edit_url"
    else:
        return {"status": "error", "message": "Album not found"}
    albums_coll = MongoLoad({url_type: album_id})
    albums = await list(albums_coll.retrieve(coll_albums, limit=1))
    if len(albums) == 0:
        return {"status": "error", "message": "Album not found"}
    if url_type == "view_url":
        albums[0].pop("edit_url")
    return {"album": albums[0], "status": "success"}


@router.post("/delete_album/{album_id}/{creator}")
async def delete_album(request: Request, album_id: str, creator: str):
    if album_id[0] != "e":
        return {"status": "error", "message": "Album can't be deleted with view url"}
    delete_images_from_album(album_id)
    albums_coll = MongoRemove({"edit_url": album_id})
    await albums_coll.remove(coll_albums)
    users_coll = MongoLoad({"username": creator})
    users = await list(users_coll.retrieve(coll_users, limit=1))
    if len(users) == 1:
        albums = users[0]["albums"]
        albums.pop(album_id)
        db_update = MongoUpd({"username": creator}, {"$set": {"albums": albums}})
        await db_update.singleval_upd(coll_users)
    return {"status": "success"}


@router.post("/create_album", response_class=RedirectResponse)
async def create_album(request: Request, album_name: str = Form(...)):
    album_name = album_name.strip()
    if album_name == "":
        return RedirectResponse(
            url=request.url_for("home_page"), status_code=status.HTTP_302_FOUND
        )
    username = await get_username(request)
    view_url = f"v{uuid.uuid4().hex}"
    edit_url = f"e{uuid.uuid4().hex}"
    album = {
        "name": album_name,
        "view_url": view_url,
        "edit_url": edit_url,
        "images": [],
        "creator": username,
    }
    documents = MongoSave([album])
    await documents.storeindb(coll_albums)
    albums = await get_albums(request)
    albums[edit_url] = album_name
    db_update = MongoUpd({"username": username}, {"$set": {"albums": albums}})
    await db_update.singleval_upd(coll_users)
    return RedirectResponse(url=f"/album/{edit_url}", status_code=status.HTTP_302_FOUND)


async def add_images_album(url_list, album_id):
    if album_id[0] == "v":
        url_type = "view_url"
    elif album_id[0] == "e":
        url_type = "edit_url"
    else:
        return {"status": "error", "message": "Album not found"}
    try:
        db_update = MongoUpd(
            {url_type: album_id}, {"$addToSet": {"images": {"$each": url_list}}}
        )
        await db_update.singleval_upd(coll_albums)
        return {"status": "success"}
    except:
        return {"status": "error", "message": "Album not found"}


async def delete_images_from_album(album_id):
    albums_coll = MongoLoad({"edit_url": album_id})
    albums = await list(albums_coll.retrieve(coll_albums, limit=1))
    if len(albums) != 0:
        list_url = albums[0]["images"]
        try:
            for url in list_url:
                name = url.split("/")[-1]
                list_imgs = await image_kit.list_files(
                    options=SearchImg(search_query=f'name="{name}"')
                ).list
                img_id = list_imgs[0].file_id
                image_kit.delete_file(file_id=img_id)
        except:
            pass
