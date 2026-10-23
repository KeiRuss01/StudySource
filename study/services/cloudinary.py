import hashlib
import os
import time

import requests


class CloudinaryError(Exception):
    pass


def configured():
    return all(
        os.getenv(name)
        for name in (
            "CLOUDINARY_CLOUD_NAME",
            "CLOUDINARY_API_KEY",
            "CLOUDINARY_API_SECRET",
        )
    )


def _signature(params):
    payload = "&".join(
        f"{key}={params[key]}" for key in sorted(params)
        if params[key] not in (None, "")
    )
    return hashlib.sha1(
        f"{payload}{os.getenv('CLOUDINARY_API_SECRET')}".encode()
    ).hexdigest()


def upload_image(uploaded_file, folder_name):
    timestamp = int(time.time())
    params = {
        "folder": folder_name,
        "timestamp": timestamp,
    }
    response = requests.post(
        "https://api.cloudinary.com/v1_1/"
        f"{os.getenv('CLOUDINARY_CLOUD_NAME')}/image/upload",
        data={
            **params,
            "api_key": os.getenv("CLOUDINARY_API_KEY"),
            "signature": _signature(params),
        },
        files={"file": uploaded_file},
        timeout=30,
    )
    if not response.ok:
        raise CloudinaryError("Cloudinary could not upload this image.")
    return response.json()


def delete_image(public_id):
    timestamp = int(time.time())
    params = {"public_id": public_id, "timestamp": timestamp}
    response = requests.post(
        "https://api.cloudinary.com/v1_1/"
        f"{os.getenv('CLOUDINARY_CLOUD_NAME')}/image/destroy",
        data={
            **params,
            "api_key": os.getenv("CLOUDINARY_API_KEY"),
            "signature": _signature(params),
        },
        timeout=15,
    )
    if not response.ok:
        raise CloudinaryError("Cloudinary could not delete this image.")
