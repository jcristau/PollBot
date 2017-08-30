from functools import partial
from pollbot.utils import (build_version_id, Channel, Status, get_version_channel,
                           get_version_from_filename)
from . import get_session, heartbeat_factory, build_task_response, build_task_response_from_bool


async def archives(product, version):
    with get_session() as session:
        channel = get_version_channel(version)
        if channel is Channel.NIGHTLY:
            return await archives_date_l10n(product, version)
        else:
            url = 'https://archive.mozilla.org/pub/{}/releases/{}/'.format(product, version)
            async with session.get(url) as resp:
                status = resp.status != 404
                exists_message = "An archive for version {} exists at {}".format(version, url)
                missing_message = ("No archive found for this version number at "
                                   "https://archive.mozilla.org/pub/{}/releases/".format(product))
                return build_task_response_from_bool(status, exists_message, missing_message, url)


async def check_nightly_archives(url, product, version):
    with get_session() as session:
        channel = get_version_channel(version)
        url = url.format(product)
        if channel is Channel.NIGHTLY:
            async with session.get(url, headers={"Accept": "application/json"}) as resp:
                if resp.status != 200:
                    status = False
                else:
                    body = await resp.json()
                    files = sorted([(r["last_modified"], r["name"]) for r in body["files"]
                                    if r["name"].startswith("{}-".format(product))],
                                   key=lambda x: x[0],
                                   reverse=True)
                    last_release = get_version_from_filename(files[0][1])
                    status = build_version_id(last_release) >= build_version_id(version)

                exists_message = "The archive exists at {}".format(url)
                missing_message = "No archive found at {}".format(url)
                return build_task_response_from_bool(status, exists_message, missing_message, url)
        else:
            return build_task_response(
                status=Status.MISSING,
                message="No archive-date checks for {} releases".format(channel.value.lower()),
                link=url)


archives_date = partial(check_nightly_archives,
                        'https://archive.mozilla.org/pub/{}/nightly/latest-date/')
archives_date_l10n = partial(check_nightly_archives,
                             'https://archive.mozilla.org/pub/{}/nightly/latest-date-l10n/')


heartbeat = heartbeat_factory('https://archive.mozilla.org/pub/firefox/releases/')
