
from os import name
from app.data.dbmodels import Storage, StorageStatus, StorageType, StorageSlot, User
from app.data.storage_type import StorageTypeAccess
from app.data.storage_slot import StorageSlotAccess
from app.data.user import UserAccess
from app.data.storage import StorageAccess, UserCantReserve, SlotAlreadyInUse, SlotDisabled
from datetime import datetime, timedelta

from .fixtures import *
from ..utils.randoms import random_string

def _type(session, name="Project Storage", location="South Workshop", days=7):
    typeaccess = StorageTypeAccess(session)
    test_st = StorageType(
        name = name,
        location = location,
        valid_days = days
    )
    return typeaccess.create(test_st)

def _slot(session, slottype, name="A-1"):
    slotaccess = StorageSlotAccess(session)
    test_slot = StorageSlot(
        name = name,
        storage_type = slottype
    )
    return slotaccess.create(test_slot)
def _user(session, username="testuser"):
    useraccess = UserAccess(session)
    u = User(
            username = username,
            displayname = "test user",
            email = "test@example.com",
            phone="123-456-7890",

        )
    return useraccess.create_user(u)


def test_create_storage(session):
    testtype = _type(session)
    testslot = _slot(session,testtype)
    testuser = _user(session)

    storageaccess = StorageAccess(session)
    s = Storage(
        user = testuser,
        slot = testslot 
    )
    created = storageaccess.create_storage(s)

    assert created.id != -1
    assert created.user == testuser
    assert created.user.id == testuser.id
    assert created.slot == testslot
    assert created.slot.id == testslot.id
    assert created.expiring > datetime.now() + timedelta(hours=6*24 + 23.9)
    assert created.expiring < datetime.now() + timedelta(days=7)

def test_get_storage(session):
    testtype = _type(session)
    testslot = _slot(session,testtype)
    testuser = _user(session)

    storageaccess = StorageAccess(session)
    s = Storage(
        user = testuser,
        slot = testslot 
    )
    created = storageaccess.create_storage(s)
    retrieved = storageaccess.get_storage_by_id(created.id)

    assert created == retrieved

def test_user_cant_reserve(session):
    testtype = _type(session)
    testslot = _slot(session,testtype)
    testuser = _user(session)
    useraccess = user.UserAccess(session)
    testuser.is_banned = True
    useraccess.update_user(testuser)

    storageaccess = StorageAccess(session)
    s = Storage(
        user = testuser,
        slot = testslot 
    )
    with pytest.raises(UserCantReserve):
        created = storageaccess.create_storage(s)

    testuser.is_banned = False
    testuser.is_active = False
    useraccess.update_user(testuser)
    s.user = testuser
    with pytest.raises(UserCantReserve):
        created = storageaccess.create_storage(s)

def test_slot_in_use(session):
    testtype = _type(session)
    testslot = _slot(session,testtype)
    testuser = _user(session)
    testuser2 = _user(session, username="testuser2")

    storageaccess = StorageAccess(session)

    s = Storage(
        user = testuser,
        slot = testslot 
    )
    created = storageaccess.create_storage(s)

    s = Storage(
        user = testuser2,
        slot = testslot
    )
    with pytest.raises(SlotAlreadyInUse):
        created = storageaccess.create_storage(s)

def test_slot_disabled(session):
    testtype = _type(session)
    testslot = _slot(session,testtype)
    testuser = _user(session)
    slotaccess = StorageSlotAccess(session)
    testslot.enabled = False
    slotaccess.update(testslot)

    storageaccess = StorageAccess(session)

    s = Storage(
        user = testuser,
        slot = testslot 
    )
    with pytest.raises(SlotDisabled):
        created = storageaccess.create_storage(s)

def test_get_storage_by_user(session):
    testtype = _type(session)
    users = [ _user(session), _user(session, username="username2") ]

    storageaccess = StorageAccess(session)

    for i in range(0,100):
        s = (StorageStatus.active if i % 5 == 0 else StorageStatus.closed)
        storageaccess.create_storage( Storage(
            user = users[i%2],
            slot = _slot(session, testtype, name=random_string(10)),
            status = s
        ))
    
    results = storageaccess.get_storage(users[0])
    active_results = storageaccess.get_storage(users[1], only_active=True)

    assert len(results) == 50
    assert all(s.user == users[0] for s in results)

    assert len(active_results) == 10
    assert all(s.user == users[1] for s in active_results)
    assert all(s.status == StorageStatus.active for s in active_results)


def test_get_all_active(session):
    testtype = _type(session)
    user = _user(session)
    statuses = [
        StorageStatus.active, 
        StorageStatus.expired,
        StorageStatus.closed,
        StorageStatus.pending
    ]
    storageaccess = StorageAccess(session)

    for i in range(0,100):
   
        storageaccess.create_storage( Storage(
            user = user,
            slot = _slot(session, testtype, name=random_string(10)),
            status = statuses[i%4]
        ))
    
    results = storageaccess.get_all_active()

    assert len(results) == 75
    assert all(s.status != StorageStatus.closed for s in results)

def test_update(session):
    testtype = _type(session)
    testslot = _slot(session,testtype)
    testuser = _user(session)

    storageaccess = StorageAccess(session)
    s = Storage(
        user = testuser,
        slot = testslot 
    )
    created = storageaccess.create_storage(s)
    created.status = StorageStatus.closed
    updated = storageaccess.update(created)

    assert created == updated
    assert updated != s
    assert updated.id == 1

def test_bad_update(session):
    testtype = _type(session)
    testslot = _slot(session,testtype)
    testuser = _user(session)

    storageaccess = StorageAccess(session)
    s = Storage(
        user = testuser,
        slot = testslot 
    )
    with pytest.raises(KeyError):
        updated = storageaccess.update(s)

def test_bad_get_by_id(session):
    storageaccess = StorageAccess(session)
    results = storageaccess.get_storage_by_id(-1)

    assert results is None