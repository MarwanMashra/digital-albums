from cryptography.fernet import Fernet
from imagekitio import ImageKit
from imagekitio.models.ListAndSearchFileRequestOptions import (
    ListAndSearchFileRequestOptions as SearchImg,
)


# key = "7l3WaUBEYQvs9As1p4kGabxw0rKKyMc_-Mi1tqp-Tn0=".encode()
key = Fernet.generate_key()


image_kit = ImageKit(
    private_key="private_a0ZWNDtYh5zV1PafhpLhCOpyRic=",
    public_key="public_2Y5OO3C4BmvY4xpzn3dgEAk2qng=",
    url_endpoint="https://ik.imagekit.io/MyDigitalAlbums",
)

coll_users = "users"
coll_albums = "albums"
cookie_name = "access-token"


def encrypt(message):
    fernet = Fernet(key)
    encMessage = fernet.encrypt(message.encode())
    return encMessage


def decrypt(encMessage):
    fernet = Fernet(key)
    decMessage = fernet.decrypt(encMessage).decode()
    return decMessage


def get_cookie(request):
    hashed_username = request.cookies.get(cookie_name)
    if hashed_username is None:
        return hashed_username
    else:
        return decrypt(hashed_username)


def set_cookie(response, username):
    response.set_cookie(
        key=cookie_name, value=str(encrypt(username))[2:-1], httponly=True
    )
    return response
