from __future__ import annotations

from pydantic import BaseModel, Field


class AccountCreate(BaseModel):
    display_name: str = Field(min_length=1)
    platform: str = "telegram"
    phone: str | None = None
    api_id: str | None = None
    api_hash: str | None = None
    page_access_token: str | None = None
    page_id: str | None = None
    fb_app_secret: str | None = None


class AccountUpdate(BaseModel):
    display_name: str | None = None
    platform: str | None = None
    phone: str | None = None
    api_id: str | None = None
    api_hash: str | None = None
    page_access_token: str | None = None
    page_id: str | None = None
    fb_app_secret: str | None = None


class RequestCodePayload(BaseModel):
    phone: str | None = None


class ConfirmCodePayload(BaseModel):
    phone: str | None = None
    code: str = Field(min_length=1)


class ConfirmPasswordPayload(BaseModel):
    password: str = Field(min_length=1)


class SyncPayload(BaseModel):
    full_history: bool = False


class ForwardPayload(BaseModel):
    target_chat_id: int


class DeleteMessagePayload(BaseModel):
    delete_for_everyone: bool = False
    account_id: int | None = None
    chat_id: int | None = None
    telegram_message_id: str | None = None


class RenameChatPayload(BaseModel):
    display_name: str = Field(min_length=1, max_length=128)
    sync_telegram: bool = False


class FacebookConnectPayload(BaseModel):
    page_access_token: str = Field(min_length=1)
    page_id: str | None = None
    fb_app_secret: str | None = None


class FacebookConnectPagePayload(BaseModel):
    fb_user_token: str = Field(min_length=1)
    page_id: str = Field(min_length=1)
    page_name: str | None = None

