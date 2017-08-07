import aiohttp
from pyquery import PyQuery as pq
from pollbot.exceptions import TaskError
from pollbot.utils import build_version_id


async def release_notes_published(product, version):
    with aiohttp.ClientSession() as session:
        url = 'https://www.mozilla.org/en-US/{}/{}/releasenotes/'.format(product, version)
        async with session.get(url) as resp:
            return resp.status != 404


async def security_advisories_published(product, version):
    with aiohttp.ClientSession() as session:
        url = 'https://www.mozilla.org/en-US/security/known-vulnerabilities/{}/'.format(product)
        async with session.get(url) as resp:
            if resp.status != 200:
                msg = 'Security advisories page not available  ({})'.format(resp.status)
                raise TaskError(msg)
            # Does the content contains the version number?
            body = await resp.text()
            d = pq(body)
            last_release = d("html").attr('data-latest-firefox')
            return build_version_id(last_release) >= build_version_id(version)
