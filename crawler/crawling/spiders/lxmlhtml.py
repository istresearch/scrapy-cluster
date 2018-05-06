"""
Custom overrides for Link extractors based on lxml.html
"""

from scrapy.linkextractors.lxmlhtml import LxmlParserLinkExtractor
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from scrapy.link import Link
from six.moves.urllib.parse import urljoin
from scrapy.utils.python import unique as unique_list, to_native_str
import lxml.etree as etree
from scrapy.utils.misc import rel_has_nofollow

_collect_string_content = etree.XPath("string()")


class CustomParser(LxmlParserLinkExtractor):

    def _extract_links(self, selector, response_url, response_encoding, base_url):
        '''
        Pretty much the same function, just added 'ignore' to to_native_str()
        '''
        links = []
        # hacky way to get the underlying lxml parsed document
        for el, attr, attr_val in self._iter_links(selector.root):
            # pseudo lxml.html.HtmlElement.make_links_absolute(base_url)
            try:
                # Remove leading and trailing white spaces
                # https://www.w3.org/TR/2014/REC-html5-20141028/infrastructure.html#strip-leading-and-trailing-whitespace
                attr_val = attr_val.strip()
                # Join base url and collected link
                attr_val = urljoin(base_url, attr_val)
            except ValueError:
                continue # skipping bogus links
            else:
                url = self.process_attr(attr_val)
                if url is None:
                    continue
            # added 'ignore' to encoding errors
            url = to_native_str(url, encoding=response_encoding,
                                errors='ignore')
            # to fix relative links after process_value
            url = urljoin(response_url, url)
            link = Link(url, _collect_string_content(el) or u'',
                        nofollow=rel_has_nofollow(el.get('rel')))
            links.append(link)
        return self._deduplicate_if_needed(links)

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
