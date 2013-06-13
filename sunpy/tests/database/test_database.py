from __future__ import absolute_import

import pytest

from sunpy.database import Database, EntryAlreadyAddedError,\
    EntryAlreadyStarredError
from sunpy.database.tables import DatabaseEntry
from sunpy.database.commands import NoSuchEntryError
from sunpy.database.caching import LRUCache, LFUCache


@pytest.fixture
def database_without_tables():
    return Database('sqlite:///:memory:')


@pytest.fixture
def database_using_lrucache():
    d = Database('sqlite:///:memory:', LRUCache, cache_size=3)
    d.create_tables()
    return d


@pytest.fixture
def database_using_lfucache():
    d = Database('sqlite:///:memory:', LFUCache, cache_size=3)
    d.create_tables()
    return d


@pytest.fixture
def database():
    d = Database('sqlite:///:memory:')
    d.create_tables()
    return d


def test_create_tables(database_without_tables):
    assert not database_without_tables._engine.has_table('data')
    database_without_tables.create_tables()
    assert database_without_tables._engine.has_table('data')


def test_star_entry(database):
    entry = DatabaseEntry()
    assert not entry.starred
    database.star(entry)
    assert entry.starred


def test_star_already_starred_entry(database):
    entry = DatabaseEntry()
    database.star(entry)
    with pytest.raises(EntryAlreadyStarredError):
        database.star(entry)


def test_get_starred_entries(database):
    entry1 = DatabaseEntry()
    entry2 = DatabaseEntry()
    database.add(entry1)
    database.add(entry2)
    assert list(database.get_starred()) == []
    database.star(entry2)
    assert list(database.get_starred()) == [entry2]


def test_add_entry(database):
    entry = DatabaseEntry()
    assert entry.id is None
    database.add(entry)
    database.commit()
    assert entry.id == 1


def test_add_already_existing_entry(database):
    entry = DatabaseEntry()
    database.add(entry)
    database.commit()
    with pytest.raises(EntryAlreadyAddedError):
        database.add(entry)


def test_edit_entry(database):
    entry = DatabaseEntry()
    database.add(entry)
    database.commit()
    assert entry.id == 1
    database.edit(entry, id=42)
    assert entry.id == 42


def test_remove_existing_entry(database):
    entry = DatabaseEntry()
    database.add(entry)
    assert database.session.query(DatabaseEntry).count() == 1
    assert entry.id == 1
    database.remove(entry)
    assert database.session.query(DatabaseEntry).count() == 0


def test_remove_nonexisting_entry(database):
    with pytest.raises(NoSuchEntryError):
        database.remove(DatabaseEntry())


def test_iter(database):
    entry1 = DatabaseEntry()
    entry2 = DatabaseEntry()
    database.add(entry1)
    database.add(entry2)
    expected_entries = [entry1, entry2]
    entries = list(database)
    assert entries == expected_entries


def test_len(database):
    assert len(database) == 0
    database.session.add(DatabaseEntry())
    assert len(database) == 1


def test_lru_cache(database_using_lrucache):
    assert not database_using_lrucache._cache
    entry1, entry2, entry3 = DatabaseEntry(), DatabaseEntry(), DatabaseEntry()
    database_using_lrucache.add(entry1)
    database_using_lrucache.add(entry2)
    database_using_lrucache.add(entry3)
    assert len(database_using_lrucache) == 3
    entries = list(database_using_lrucache)
    assert entries[0] == entry1
    assert entries[1] == entry2
    assert entries[2] == entry3
    #assert database_using_lrucache._cache.items() == [
    #    (1, entry1), (2, entry2), (3, entry3)]
    database_using_lrucache.get_entry_by_id(1)
    database_using_lrucache.get_entry_by_id(3)
    entry4 = DatabaseEntry()
    database_using_lrucache.add(entry4)
    assert len(database_using_lrucache) == 3
    entries = list(database_using_lrucache)
    assert entries[0] == entry1
    assert entries[1] == entry3
    assert entries[2] == entry4
    #assert database_using_lrucache._cache.items() == [
    #    (1, entry1), (3, entry3), (4, entry4)]


def test_lfu_cache(database_using_lfucache):
    assert not database_using_lfucache._cache
    entry1, entry2, entry3 = DatabaseEntry(), DatabaseEntry(), DatabaseEntry()
    database_using_lfucache.add(entry1)
    database_using_lfucache.add(entry2)
    database_using_lfucache.add(entry3)
    assert len(database_using_lfucache) == 3
    entries = list(database_using_lfucache)
    assert entries[0] == entry1
    assert entries[1] == entry2
    assert entries[2] == entry3
    #assert database_using_lrucache._cache.items() == [
    #    (1, entry1), (2, entry2), (3, entry3)]
    # access the entries #1 and #2 to increment their counters
    database_using_lfucache.get_entry_by_id(1)
    database_using_lfucache.get_entry_by_id(2)
    entry4 = DatabaseEntry()
    database_using_lfucache.add(entry4)
    assert len(database_using_lfucache) == 3
    entries = list(database_using_lfucache)
    assert entries[0] == entry1
    assert entries[1] == entry2
    assert entries[2] == entry4
    #assert database_using_lrucache._cache.items() == [
    #    (1, entry1), (2, entry2), (4, entry4)]