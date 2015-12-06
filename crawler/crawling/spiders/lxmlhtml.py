"""
Custom overrides for Link extractors based on lxml.html
"""

from scrapy.linkextractors.lxmlhtml import LxmlParserLinkExtractor
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from scrapy.link import Link
from six.moves.urllib.parse import urljoin
from scrapy.utils.python import unique as unique_list
import lxml.etree as etree

_collect_string_content = etree.XPath("string()")


class CustomParser(LxmlParserLinkExtractor):

    def _extract_links(self, selector, response_url, response_encoding, base_url):
        '''
        Pretty much the same function, just added 'ignore' to url.encode
        '''
        links = []
        # hacky way to get the underlying lxml parsed document
        for el, attr, attr_val in self._iter_links(selector._root):
            # pseudo lxml.html.HtmlElement.make_links_absolute(base_url)
            try:
                attr_val = urljoin(base_url, attr_val)
            except ValueError:
                continue  # skipping bogus links
            else:
                url = self.process_attr(attr_val)
                if url is None:
                    continue
            if isinstance(url, unicode):
                # add 'ignore' to encoding errors
                url = url.encode(response_encoding, 'ignore')
            # to fix relative links after process_value
            url = urljoin(response_url, url)
            link = Link(url, _collect_string_content(el) or u'',
                        nofollow=True if el.get('rel') == 'nofollow' else False)
            links.append(link)

        return unique_list(links, key=lambda link: link.url) \
                if self.unique else links


class CustomLxmlLinkExtractor(LxmlLinkExtractor):
    def __init__(self, allow=(), deny=(), allow_domains=(), deny_domains=(),
                 restrict_xpaths=(),
                 tags=('a', 'area'), attrs=('href',), canonicalize=True,
                 unique=True, process_value=None, deny_extensions=None,
                 restrict_css=()):
        super(CustomLxmlLinkExtractor, self).__init__(allow=allow, deny=deny,
                allow_domains=allow_domains, deny_domains=deny_domains,
                restrict_xpaths=restrict_xpaths, restrict_css=restrict_css,
                canonicalize=canonicalize, deny_extensions=deny_extensions)
        tag_func = lambda x: x in tags
        attr_func = lambda x: x in attrs

        # custom parser override
        cp = CustomParser(tag=tag_func, attr=attr_func,
                          unique=unique, process=process_value)
        self.link_extractor = cp
