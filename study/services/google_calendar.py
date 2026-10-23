import os
from datetime import timedelta
from urllib.parse import urlencode

import requests
from django.utils import timezone as django_timezone


class GoogleCalendarError(Exception):
    pass


def configured():
    return bool(os.getenv("GOOGLE_CLIENT_ID") and os.getenv("GOOGLE_CLIENT_SECRET"))


def authorization_url(state):
    params = {
        "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
        "redirect_uri": os.getenv("GOOGLE_CALENDAR_REDIRECT_URI", ""),
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/calendar.events",
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)


def exchange_code(code):
    response = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
            "redirect_uri": os.getenv("GOOGLE_CALENDAR_REDIRECT_URI", ""),
            "grant_type": "authorization_code",
        },
        timeout=15,
    )
    if not response.ok:
        raise GoogleCalendarError("Google authorization could not be completed.")
    return response.json()


def access_token(connection):
    if connection.token_expires_at and connection.token_expires_at > django_timezone.now():
        return connection.access_token
    if not connection.refresh_token:
        raise GoogleCalendarError("Please connect Google Calendar again.")
    response = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
            "refresh_token": connection.refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=15,
    )
    if not response.ok:
        raise GoogleCalendarError("Google Calendar token refresh failed.")
    data = response.json()
    connection.access_token = data["access_token"]
    connection.token_expires_at = django_timezone.now() + timedelta(
        seconds=int(data.get("expires_in", 3600)) - 60
    )
    connection.save(update_fields=["access_token", "token_expires_at", "updated_at"])
    return connection.access_token


def sync_deadline(connection, deadline):
    token = access_token(connection)
    event = {
        "summary": deadline.title,
        "description": deadline.description or "StudySource research deadline",
        "start": {"date": deadline.due_date.isoformat()},
        "end": {"date": deadline.due_date.isoformat()},
    }
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    if deadline.google_event_id:
        url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{deadline.google_event_id}"
        response = requests.put(url, headers=headers, json=event, timeout=15)
    else:
        response = requests.post(
            "https://www.googleapis.com/calendar/v3/calendars/primary/events",
            headers=headers,
            json=event,
            timeout=15,
        )
    if not response.ok:
        raise GoogleCalendarError("Google Calendar could not save this deadline.")
    return response.json()["id"]
