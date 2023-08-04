from __future__ import absolute_import, print_function

import logging
import stat
import time
import tempfile
import contextlib
from datetime import datetime, timedelta
import genericpath
import os
from pathlib import Path

import P4

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logging.basicConfig()


class CheckedOutException(Exception):
    pass


def setLoggingLevel(level):
    logger.setLevel(level)


@contextlib.contextmanager
def p4Connect(p4inst):
    """
    Context manager that connects a p4 instance on entry if it is not connected
    and disconnects on exit if it wasn't connected.

    In other words the connection state of the passed p4 instance will be preserved
    on exit.
    """
    connected = p4inst.connected()
    if not connected:
        p4inst.connect()
    try:
        yield p4inst
    finally:
        # Maintain the original connection state of p4inst
        if not connected:
            p4inst.disconnect()


def getP4inst(p4inst, **kwargs):
    """
    Returns p4inst if it is a P4 instance, otherwise instantiates a new P4
    instance using any provided keyword args.

    This is a convenience function for methods that accept an optional p4
    instance argument and want to construct one if it is not supplied.
    """
    if p4inst is None:
        return P4.P4(**kwargs)
    return p4inst


def splitrev(path):
    """
    Split the revision from a perforce pathname.

    Currently only supports the following revision syntax:
    #n (where n is an integer revision)
    #none
    #head
    #have

    Revision is everything from the last '#' to the end, ignoring
    leading pound signs.  Returns (root, rev); rev may be empty.
    """
    root, rev = genericpath.splitext(path, '\\', '/', '#')
    if rev and isValidRevision(rev):
        return Path(root), rev

    return Path(path), ''


def striprev(path):
    """
    Removes the revision (if any) from <path>.
    """
    root, rev = genericpath.splitext(path, '\\', '/', '#')
    return root


def isValidRevision(rev):
    """
    Returns true if rev is valid revision syntax.

    Currently only supports the following revision syntax:
    #n (where n is an integer revision)
    #none
    #head
    #have
    """
    if not rev:
        return False

    if rev[0] == '#':
        rev = rev[1:]

    return rev in ('none', 'head', 'have') or rev.isdigit()


def _getTempRevision(p4path, p4inst=None):
    p4inst = getP4inst(p4inst)
    root, rev = splitrev(p4path)

    root, ext = root.splitext()
    tmpFile = Path.joinpath(tempfile.gettempdir(), '%s_%s%s' % (root.name, time.time(), ext))
    with p4Connect(p4inst) as p4:
        p4.fetch_print(tmpFile, p4path)
    # print creates as a read-only file
    tmpFile.chmod(stat.S_IWRITE)

    return tmpFile


class tempRevision(Path):
    """
    Writes a perforce file to a temporary file and returns the path to that file as a
    Path object. Useful for accessing different file revisions without having to sync to them

    Can be used as a context manager (in a with statement) to have the temporary
    file deleted automatically.

    Example:

        with tempRevision('path/to/file.txt#9') as f:
            # Operate on the temporary file

        # The temporary file is automatically removed here
    """

    def __init__(self, *args, **kwargs):
        # we have to override __init__ to remove the p4inst argument that __new__
        # will pass
        if 'p4inst' in kwargs:
            del kwargs['p4inst']
        super(tempRevision, self).__init__(*args, **kwargs)

    def __new__(cls, p4path, p4inst=None, *args, **kwargs):
        # We have to override __new__ and not __init__ because Path inherits
        # from unicode, which will set its value to the first positional argument
        tmp = _getTempRevision(p4path, p4inst=p4inst)
        return super(tempRevision, cls).__new__(cls, tmp, *args, **kwargs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.exists():
            os.remove(self)


def getLatestRevision(f, p4inst=None):
    """
    Syncs to the latest revision of file(s)

    No special handling is done for paths that contain revision specifiers, meaning
    that if any path has a revision specifier, it will be synced to that revision.
    """
    if isinstance(f, str):
        f = [f]
    p4inst = getP4inst(p4inst)
    toSync = []
    logger.debug("getLatestRevision input files: %s" % f)
    with p4Connect(p4inst) as p4:
        for fstat in p4.run_fstat(f):
            logger.debug(fstat)
            if 'headRev' not in fstat:
                # Marked for add/integrate/copy/etc
                continue
            if 'haveRev' not in fstat:
                if 'delete' in fstat['headAction']:
                    # Deleted and we don't have it
                    continue
                toSync.append(fstat['depotFile'])
            elif fstat['haveRev'] != fstat['headRev']:
                toSync.append(fstat['depotFile'])

        if toSync:
            logger.debug("Syncing:\n%s" % '\n'.join(toSync))
            return p4.run_sync(toSync)

    return []


def lookup_rev(depotpath, change=None, description=None, p4inst=None):
    """
    Return the revision number for depotpath at change
    """
    with p4Connect(p4inst) as p4inst:
        log = p4inst.run_filelog(depotpath)[0]
    if change is not None:
        for rev in log.revisions:
            if rev.change == change:
                return rev.rev
    if description is not None:
        for rev in log.revisions:
            if description.upper() in rev.desc.upper():
                return rev.rev


def lookup_change(depotpath, rev, p4inst=None):
    """
    Return the change number for the depotpath at revision rev
    """
    with p4Connect(p4inst) as p4inst:
        log = p4inst.run_filelog(depotpath)[0]
    for revision in log.revisions:
        if revision.rev == rev:
            return revision.change


def get_date_added(depotpath, p4inst):
    """
    Return a datetime object for when the file was originally added to Perforce
    """
    with p4Connect(p4inst) as p4inst:
        log = p4inst.run_filelog(depotpath)
    if log[-1].revisions[-1].integrations:
        return get_date_added(log[-1].revisions[-1].integrations[-1].file, p4inst)
    return log[-1].revisions[-1].time


def createChangelist(description, p4inst=None):
    """
    Creates a changelist with the supplied description
    """
    p4 = getP4inst(p4inst)
    with p4Connect(p4) as p4:
        # encode to get rid of weird characters that copying from outlook can cause
        # decode to make sure we don't end up with a bytes string in py 3
        change = {"Description": str(description.encode('ascii', 'ignore').decode()), "Change": "new"}
        res = p4.save_change(change)
        if len(res) > 1:
            res = next([r] for r in res if r.startswith('Change'))
        if res:
            return p4.fetch_changelist(int(res[0].split()[1]))

    raise P4.P4Exception("Could not create changelist")


def getChangelists(status='pending', user=None, p4inst=None):
    """
    Returns a list of changelists. The format of the returned changelists match
    that of the `p4 change` command.

    status: Limit the result to the changelists with the given status
         (pending, submitted, or shelved). Default pending
    user: List only changes made by named user. If None, the current user will be used
    """
    p4 = getP4inst(p4inst)
    args = []
    if user is None:
        user = p4.user
    if user == p4.user:
        client = p4.client  # restrict to current workspace is using current user
        args.extend(['-c', client])
    if status is not None:
        args.extend(['-s', status])
    args.extend(['-u', user])
    changelists = []
    with p4Connect(p4):
        for change in p4.run_changes(*args):
            changelists.append(p4.fetch_change(change['change']))

    return changelists


def getChangelistsWithDescription(desc, status='pending', user=None, ignorecase=False, p4inst=None):
    """
    Returns changelists that match the given description. The format of the returned
    changelist(s) match that of the `p4 change` command

    status: Limit the result to the changelists with the given status
         (pending, submitted, or shelved). If status is None, changelists with
         any status will be returned. Default pending
    user: List only changes made by named user. If None, the current user will be used
    ignorecase: Whether the description comparison should be case-insensitive or not
    """
    p4 = getP4inst(p4inst)
    args = ['-l']
    if user is None:
        user = p4.user
    if user == p4.user:
        client = p4.client  # restrict to current workspace is using current user
        args.extend(['-c', client])
    if status is not None:
        args.extend(['-s', status])
    args.extend(['-u', user])
    if ignorecase:
        desc = desc.lower()
    changelists = []
    with p4Connect(p4):
        for change in p4.run_changes(*args):
            if ignorecase:
                change['desc'] = change['desc'].lower()
            if desc.strip() == change['desc'].strip():
                changelists.append(change)

        changelists = [p4.fetch_change(c['change']) for c in changelists]
    return changelists


def getChangelistWithDescription(desc, status='pending', user=None, ignorecase=False, create=False, p4inst=None):
    """
    Returns the changelist that matches the description. If multiple matches
    are found, the most recent changelist will be returned.
    If no matches are found and <create> is True, a changelist with the description
    will be created.
    """
    p4inst = getP4inst(p4inst)
    changelists = getChangelistsWithDescription(desc, status=status, user=user, ignorecase=ignorecase, p4inst=p4inst)
    if changelists:
        # changelists are returned sorted by data-descending, so the first element
        # will always be the most recent
        return changelists[0]
    elif create:
        return createChangelist(desc, p4inst=p4inst)


def updateChangelistDescription(changeid, description, p4inst):
    """Updates the description of a pending changelist"""
    with p4Connect(p4inst) as p4:
        change = p4inst.fetch_change(changeid)
        if change['Status'] != 'pending':
            raise Exception(
                "Can only update the status of a pending changelist, not '{0}' ({1})".format(change['Status'], changeid)
            )
        change['Description'] = description
        p4.save_change(change)


def getClientPath(path, p4inst=None):
    """
    Returns the local path to a given file
    """
    p4 = getP4inst(p4inst)
    with p4Connect(p4):
        return p4.run_fstat('-T', 'clientFile', path)[0]['clientFile']


def getDepotPath(path, p4inst=None):
    """
    Returns the depot path to a given file
    """
    p4 = getP4inst(p4inst)
    with p4Connect(p4):
        return p4.run_fstat('-T', 'depotFile', path)[0]['depotFile']


def p4EditOrAdd(fpaths, changeid=None, p4inst=None, exclusive=True, check_permissions=False):
    """Marks one or more files for edit if it is tracked by p4 or add if it is not"""
    with p4Connect(getP4inst(p4inst)) as p4:
        with p4.at_exception_level(1):
            # if fpaths is a string wrap it in a list
            if isinstance(fpaths, (str, os.PathLike)):
                if isinstance(fpaths, os.PathLike):
                    fpaths = str(fpaths)
                fpaths = [fpaths]
            expanded_fpaths = []
            for fpath in fpaths:
                # to prevent issues with fstat we need to expand wildcards
                # to find the local files we need to sync file patterns
                p4inst.run_sync(fpath)
                fpath = p4inst.run_where(fpath)[0]['path']
                fpath = fpath.replace('%%1', '*').replace('%%2', '*')
                if '...' in fpath or '*' in fpath:
                    dots = fpath.index('...') if '...' in fpath else len(fpath)
                    star = fpath.index('*') if '*' in fpath else len(fpath)
                    first_wildcard = min([dots, star])
                    pattern = fpath[first_wildcard:]
                    fpath = Path(fpath[:first_wildcard])
                    # not an exact equivalent since ... is 1+ directories and ** is 0+ directories
                    pattern = pattern.replace('...', '**')
                    if pattern.endswith('**'):
                        pattern = pattern[:-3] + '**\\*'
                    for match in fpath.rglob(pattern):
                        if match.is_file():
                            expanded_fpaths.append(str(match))
                else:
                    expanded_fpaths.append(fpath)
            results = []
            for fpath in expanded_fpaths:
                if changeid:
                    args = ['-c', changeid, fpath]
                else:
                    args = [fpath]
                fstats = p4.run_fstat(fpath)
                if fstats:
                    fstat = fstats[0]
                    if 'action' in fstat:
                        if fstat.get('action') == 'branch' or fstat.get('action') == 'integrate':
                            results.extend(p4.run_edit(*args))
                        continue
                    elif 'otherOpen' in fstat and (exclusive or '+l' in fstat['headType']):
                        # check the file permissions
                        raise CheckedOutException(
                            "File is opened by another user ({0}): {1}".format(fstat['otherOpen'], fpath)
                        )
                    elif 'headAction' not in fstat or 'delete' in fstat['headAction']:
                        # Opened for add/move by another user, or it has been deleted
                        results.extend(p4.run_add(*args))
                    else:
                        results.extend(p4.run_edit(*args))
                else:
                    # use p4 opened -a filepath to see if another user has the file open for add
                    opened = p4.run_opened('-a', fpath)
                    # QUESTION - Do we want to add the file if it isn't exclusive?
                    #            If yes, we need to check if +l is in opened[0]['type'] be for raising
                    #            if opened and '+l' in opened[0]['type']:
                    if opened and (exclusive or '+l' in opened[0]['type']):
                        raise CheckedOutException(
                            'File is opened by another user ({0}@{1}): {2}'.format(
                                opened[0]['user'], opened[0]['client'], fpath
                            )
                        )
                    results.extend(p4.run_add(*args))

                if check_permissions:
                    local = p4.run_where(fpath)[0]['path']
                    if os.path.isfile(local):
                        os.chmod(local, stat.S_IWRITE)

            if not results:
                return None
            return results


def sync_and_clobber(paths, p4inst=None):
    """
    Sync files and clobber any that are locally writable or missing.
    Basically a force sync but only on files that have changed on the server.
    """
    if not paths:
        # prevent syncing the entire workspace
        return
    p4 = getP4inst(p4inst)
    with p4Connect(p4) as p4:
        with p4.at_exception_level(1):
            dry_run = p4.run_sync('-n', paths)
        if isinstance(dry_run, str):
            raise ValueError(dry_run)
        paths_to_sync = []
        for result in dry_run:
            if isinstance(result, str):
                raise ValueError(result)
            # if the file is deleted at this revision, rev lists the last existing revision so sync ot rev 0
            if result['action'] == 'deleted':
                paths_to_sync.append(f"{result['depotFile']}#0")
            else:
                paths_to_sync.append(f"{result['depotFile']}#{result['rev']}")
        missing = p4.run_diff('-sd', paths)
        paths_to_sync.extend([f"{result['depotFile']}#{result['rev']}" for result in missing])
        if paths_to_sync:
            result = p4.run_sync('-f', paths_to_sync)
            return result


def moveOutdatedFilesToNewChangeList(p4c, changeid, newchangeid=None):
    """
    Move any files in the given changelist that are not the latest revision to
    a new changelist.

    Args:
        p4c (p4 instance): The p4 instance to use.
        changeid (number): The changelist to use.
        newchangeid (number, optional): Move outdated files to this changelist.
            If missing a new changelist is created.
    """
    with p4Connect(p4c):
        # get the change description
        if not newchangeid:
            desc = p4c.run_describe(changeid)[0]['desc']
            newchangeid = getChangelistWithDescription(desc.strip() + ' outdated files', create=True, p4inst=p4c)[
                'Change'
            ]

        # shelved changes
        changes = p4c.run_describe('-S', changeid)
        if changes and 'rev' in changes[0]:
            for rev, file in zip(changes[0]['rev'], changes[0]['depotFile']):
                files = p4c.run_files(file)
                if not files:
                    print('no files for %s' % file)
                    continue
                depot_info = files[0]
                if rev != depot_info['rev']:
                    # print rev, file
                    # unshelve to the new changelist
                    p4c.run_unshelve('-s', changeid, '-f', '-c', newchangeid, file)
                    # re-shelve it and revert
                    p4c.run_shelve('-c', newchangeid, file)
                    p4c.run_revert('-c', newchangeid, file)
                    # remove from old changelist
                    p4c.run_shelve('-c', changeid, '-d', file)

        # open files
        changes = p4c.run_describe(changeid)
        # print changes
        if changes and 'rev' in changes[0]:
            # print 'unshelved'
            for rev, file in zip(changes[0]['rev'], changes[0]['depotFile']):
                depot_info = p4c.run_files(file)[0]
                print(depot_info)
                if rev != depot_info['rev']:
                    # print rev, file
                    # reopen in new changelist
                    p4c.run_reopen('-c', newchangeid, file)


def collect_shelved_changes(description, p4inst=None):
    """
    Collect shelved files from multiple changelists (and multiple workspaces)
    with the same description into a single changelist.
    """
    p4inst = getP4inst(p4inst)
    with p4Connect(p4inst) as p4inst:
        # find shelved changelists
        shelved_changes = p4inst.run_changes('-u', p4inst.user, '-s', 'shelved', '-L')
        changes_to_collect = [change for change in shelved_changes if change['desc'].strip() == description.strip()]
        if not changes_to_collect:
            return
        # make a new collection changelist
        collection_change = createChangelist('Collected: %s' % description)
        for change_to_collect in changes_to_collect:
            form = p4inst.fetch_change(change_to_collect['change'])
            if 'Files' in form:
                if not change_to_collect['client'] == p4inst.client:
                    raise P4.P4Exception('Change: %s contains non-shelved files.' % change_to_collect['change'])
                # Shelve and revert the files if the change is owned by the current client
                p4inst.run_shelve('-c', change_to_collect['change'])
                for f in form['Files']:
                    p4inst.run_revert('-c', change_to_collect['change'], f)
            # change the ownership if the current client is not the owner
            if not change_to_collect['client'] == p4inst.client:
                form['Client'] = p4inst.client
                p4inst.save_change(form)
            # sync the files before unshelving them
            describe = p4inst.run_describe('-S', change_to_collect['change'])[0]
            shelved_files = describe['depotFile']
            p4inst.run_sync(shelved_files)
            # unshelve the files into the collection change -f to clobber any writeable files
            p4inst.run_unshelve('-s', change_to_collect['change'], '-c', collection_change['Change'], '-f')
            # delete the shelved files and the original change
            p4inst.run_shelve('-d', '-c', change_to_collect['change'])
            p4inst.delete_change(change_to_collect['change'])
        # shelve and revert the files in the new collected change
        p4inst.run_shelve('-c', collection_change['Change'])
        for f in p4inst.fetch_change(collection_change['Change']).get('Files', []):
            p4inst.run_revert('-c', collection_change['Change'], f)
    return collection_change


def remove_shelved_conflicts(changeid, checkForOwners=False, p4inst=None):
    """
    Takes a change list, and compares the revision numbers of the shelved files in that list
    to the revision numbers on the server of the same file. If they are different (meaning the
    server file has been updated or rolled back since the file was shelved) then the
    shelved file is deleted.
    Returns a list of the files deleted from the shelf.
    checkForOwners: If True, will also log / delete files that are currently checked out from the server.
    """

    p4inst = getP4inst(p4inst)

    with p4Connect(p4inst) as p4inst:
        # Empty list to store deleted files
        deletedFromShelf = []
        # Pull shelved files from given change list
        changes = p4inst.run_describe('-S', changeid)
        if changes:
            # Create a tuple of each shelved file with its revision number
            for shelvedRev, dPath in zip(changes[0]['rev'], changes[0]['depotFile']):
                # Collect the current server version of the same files
                file = p4inst.run_files(dPath)
                # Current revision number
                currentRev = file[0]['rev']
                # If they are different, add the file to deletedFromShelf, then delete it
                if shelvedRev != currentRev:
                    deletedFromShelf.append(dPath)
                    p4inst.run_shelve('-c', changeid, '-d', dPath)
                    continue

                if checkForOwners:
                    owner = p4inst.run_opened('-a', dPath)
                    if owner:
                        deletedFromShelf.append(dPath)
                        p4inst.run_shelve('-c', changeid, '-d', dPath)

    return deletedFromShelf


def is_checked_out(paths, p4inst=None):
    """
    replacement function for p4helper
    the function returns a username if the file is checked out, return False otherwise.
    ignores current user and client
    Args:
        paths (str, list): paths to check
        p4inst (None, optional): p4 connection to use

    Returns:
        list of tuples: depot file and user@client
    """
    p4 = getP4inst(p4inst)
    files = []
    with p4Connect(p4):
        result = p4.run_opened('-a', paths)
        for r in result:
            # check if the file is opened by another user or in another workspace
            if not (r['user'].lower() == p4.user.lower() and r['client'].lower() == p4.client.lower()):
                files.append((r['depotFile'], '%s@%s' % (r['user'], r['client'])))

    return files


def get_available_files(paths, p4inst=None):
    """
    Replacement function for p4helper
    returns a list of files that exist and aren't checked out

    Args:
        paths (str, list): paths to check
        p4inst (None, optional): p4 connection to use

    Returns:
        list of tuples: depot file and user@client
    """
    p4 = getP4inst(p4inst)
    with p4Connect(p4):
        files = p4.run_files('-e', paths)
        files = set(f['depotFile'] for f in files)
        opened = is_checked_out(paths, p4)
        opened = set(o[0] for o in opened)
    return sorted(files - opened)


def get_revision_graph(depot_path, p4inst):
    """
    Returns a string with the revision graph information for depot_path.
    """
    import textwrap

    output = ''
    with p4Connect(p4inst):
        logs = p4inst.run_filelog('-i', '-l', depot_path)
        for log in logs:
            for revision in log.revisions:
                rev_info = textwrap.dedent(
                    '''
                    {time} - {depotFile}#{rev}
                    Change List: {change}
                    Perforce Action: {action}
                    User: {user}
                    Comment: {desc}

                    '''
                ).format(
                    time=revision.time,
                    depotFile=revision.depotFile,
                    rev=revision.rev,
                    change=revision.change,
                    action=revision.action,
                    user=revision.user,
                    desc=revision.desc,
                )
                output += rev_info
    return output


def consolidate_changelists(main_cl, cls_to_move, p4c):
    """
    Moves files from many changelists into a single changelist.

    Args:
        main_cl (int): changelist number for the changelist you want to move all the files TO.
        cls_to_move (list): a list of int changelist numbers that you want to move all the
        files FROM
        p4c (P4.P4, optional): a P4 connection object. If one is not provided, it will be
        created in the Art depot at exception level 1.
    """
    if not isinstance(cls_to_move, (list, tuple)):
        cls_to_move = [cls_to_move]
    with p4Connect(p4c):
        # detailed info about all given changelists (including files on the CL)
        source_change_infos = p4c.run_describe(cls_to_move)
        for source_change in source_change_infos:
            p4c.run_reopen('-c', main_cl, source_change['depotFile'])
            p4c.run_change('-d', source_change['change'])
    logger.info('Changelist consolidation complete. Files in CL %s' % main_cl)


def find_deleted(pattern, p4c):
    with p4Connect(p4c):
        all_records = p4c.run_files(pattern)
        existing_records = p4c.run_files('-e', pattern)
    all_files = set([r['depotFile'].lower() for r in all_records])
    existing_files = set([r['depotFile'].lower() for r in existing_records])
    deleted_files = sorted(all_files - existing_files)
    return deleted_files


def sync_deleted(pattern, p4c):
    deleted_files = find_deleted(pattern, p4c)
    if not deleted_files:
        return
    with p4Connect(p4c):
        for chunk in chunk_list(deleted_files, 50):
            p4c.run_sync(chunk)


def chunk_list(full_list, chunk_size):
    for i in range(0, len(full_list), chunk_size):
        yield full_list[i: i + chunk_size]


def delete_empty_changelists(p4c):
    """
    delete empty changelists that are more than 1 day old
    """
    one_day = timedelta(days=1)
    with p4c.connect():
        changes = p4c.run_changes('-c', p4c.client, '-u', p4c.user, '-s', 'pending')
        for change in changes:
            cl_time = datetime.fromtimestamp(float(change['time']))
            # check if the cl is at least 1 day old
            if datetime.now() - cl_time < one_day:
                continue
            # check if the cl contains files
            form = p4c.fetch_change(change['change'])
            if 'Files' in form:
                continue
            # check if the cl has shelved files
            desc = p4c.run_describe('-S', change['change'])[0]
            if 'depotFile' in desc:
                continue
            logger.info('Deleting: %s', change['change'])
            p4c.run_change('-d', change['change'])


def get_non_underscored_files(pattern, banned_strings=['/_'], p4inst=None):
    """
    Finds all files given a pattern that do not contain any of the strings in "banned_strings".
    This can help speed up syncing for folders which have many files in "_working" folders
    etc. The files in these folders are often PSDs and other such large files that are not
    necessary for building.

    Args:
        pattern (basestring): a p4-compatible file pattern.
        banned_strings (list, optional): a list of strings that should be banned from
            the filepaths. Not case-sensitive.

    Returns:
        list: a list of filepaths that match the pattern and do not have any of the
            banned strings in them.
    """
    p4c = getP4inst(p4inst)
    with p4c.connect():
        all_files = [f['depotFile'] for f in p4c.run_files('-e', pattern)]
        approved_files = []
        for file in all_files:
            if any([banned_string.lower() in file.lower() for banned_string in banned_strings]):
                continue
            else:
                approved_files.append(file)
    logger.info(f'Found {len(approved_files)} approved files with pattern "{pattern}"')
    return approved_files


def sync_non_underscored_files(pattern, preview=False, p4inst=None):
    """
    Syncs all files matching the pattern that do not have the string '/_' in the
    filepath.

    Args:
        pattern (basestring): a p4-compatible file pattern.
    """
    file_list = get_non_underscored_files(pattern)
    if file_list:
        p4c = getP4inst(p4inst)
        with p4c.connect():
            if preview:
                results = p4c.run_sync('-n', file_list)
                logger.info('%s files are out-of-date and will be synced' % len(results))
            else:
                logger.info('Syncing %s files...' % len(file_list))
                results = p4c.run_sync(file_list)
                logger.info('%s files were out-of-date' % len(results))
                logger.info('Done syncing.')
    else:
        logger.info('No files to sync.')


def unsync_underscored_files(patterns, p4inst=None):
    """
    Un-syncs all files that have an underscored folder in their depot path within the provided pattern.

    Args:
        patterns (str, or list of strs): p4-compatible file pattern. Can be a list of patterns.
    """
    logger.info('Unsync underscored files')

    if not isinstance(patterns, list):
        patterns = [patterns]

    if not p4inst:
        p4c = getP4inst(p4inst)

    with p4Connect(p4inst) as p4:
        pattern_iterator = 1
        for p in patterns:
            logger.info(f'Gathering files for pattern {pattern_iterator} of {len(patterns)}: {p}')
            filedata = [d['depotFile'] + '#0' for d in p4.run_files('-e', patterns) if '/_' in d['depotFile']]
            if filedata:
                total = len(filedata)
                logger.info(f'Files:  {total}')

                file_iterator = 0
                for i, dpaths in enumerate(chunk_list(filedata, 1000)):
                    file_iterator = file_iterator + 1000
                    print(f'Chunk {i}: Files {file_iterator} of {total}')
                    try:
                        p4.run_sync(dpaths)
                    except:
                        sync_and_clobber(dpaths, p4inst=p4)

            else:
                logger.info('Unsync list is 0 files, please check the p4 pattern.')
            pattern_iterator += 1


# ALIASES
_get_temp_rev = _getTempRevision
create_cl = createChangelist
delete_empty_cls = delete_empty_changelists
get_cls = getChangelists
get_cls_w_desc = getChangelistsWithDescription
get_cl_w_desc = getChangelistWithDescription
get_client_path = getClientPath
get_depot_path = getDepotPath
get_latest_rev = getLatestRevision
get_p4_inst = getP4inst
is_valid_rev = isValidRevision
move_outdated_files_to_new_cl = moveOutdatedFilesToNewChangeList
p4_connect = p4Connect
p4_edit_or_add = p4EditOrAdd
set_log_lvl = setLoggingLevel
split_rev = splitrev
strip_rev = striprev
update_cl_desc = updateChangelistDescription
