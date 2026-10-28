"""Read only the explicitly configured local eMAG generic credential."""
import ctypes
from ctypes import wintypes
import os

TARGET = 'IvyeaOps/eMAG/RO'


class Credential(ctypes.Structure):
    _fields_ = [
        ('Flags', wintypes.DWORD), ('Type', wintypes.DWORD),
        ('TargetName', wintypes.LPWSTR), ('Comment', wintypes.LPWSTR),
        ('LastWritten', wintypes.FILETIME), ('CredentialBlobSize', wintypes.DWORD),
        ('CredentialBlob', ctypes.POINTER(ctypes.c_ubyte)),
        ('Persist', wintypes.DWORD), ('AttributeCount', wintypes.DWORD),
        ('Attributes', ctypes.c_void_p), ('TargetAlias', wintypes.LPWSTR),
        ('UserName', wintypes.LPWSTR)]


def read_emag_credentials():
    if os.name != 'nt':
        raise OSError('Windows Credential Manager required')
    api = ctypes.WinDLL('Advapi32.dll', use_last_error=True)
    pointer = ctypes.POINTER(Credential)()
    api.CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                             ctypes.POINTER(ctypes.POINTER(Credential))]
    api.CredReadW.restype = wintypes.BOOL
    api.CredFree.argtypes = [ctypes.c_void_p]
    api.CredFree.restype = None
    if not api.CredReadW(TARGET, 1, 0, ctypes.byref(pointer)):
        raise OSError(ctypes.get_last_error(), 'Configured eMAG credential is unavailable')
    try:
        value = pointer.contents
        username = value.UserName or ''
        password = ctypes.string_at(value.CredentialBlob, value.CredentialBlobSize).decode('utf-16-le')
        if not username or not password:
            raise OSError('Configured eMAG credential is empty')
        return username, password
    finally:
        if pointer.contents.CredentialBlobSize:
            ctypes.memset(pointer.contents.CredentialBlob, 0, pointer.contents.CredentialBlobSize)
        api.CredFree(pointer)
