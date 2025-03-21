# Clairmeta - (C) YMAGIS S.A.
# See LICENSE for more information

from __future__ import absolute_import
import os
import io
import re
import xmltodict
from lxml import etree
from xml.dom.minidom import parseString
from xml.parsers.expat import ExpatError

from clairmeta.utils.sys import modified_dict, try_convert_number
from clairmeta.logger import get_log


_DEFAULT_NS_SEP = " "


def prettyprint_xml(xml_str):
    """Return a pretty-printed XML string.

    Args:
        xml_str (str): XML document string.

    Returns:
        XML document string with pretty indentation / formating.

    """
    parsed = parseString(xml_str)
    return parsed.toprettyxml(indent="  ")


def post_parse_node(path, key, value, ns_sep=_DEFAULT_NS_SEP):
    """Xmltodict postprocessor function.

    This function allow us to correct node generated by xmltodict converter
    on the fly. Direct quote from xmltodict documentation for reference :
     The optional argument `postprocessor` is a function that takes
     `path`, `key` and `value` as positional arguments and returns a
     new `(key, value)` pair where both `key` and `value` may have changed.

    Rules applied :
     - XML namespace are either replaced by alias we specify or leave as is
       if not recognized. The key will have the form
       namespace<ns_sep>key, so we extract the key to have clean dict
       keys. We store the namespace extracted as a key in the output value
       if possible (only the first time we encounter this namespace)
     - Remove UUID prefix as commonly found in DCP (urn:uuid:)
     - Try to convert string values to number
     - Replace None value by empty string

    Args:
        path (list): List of tuples for parent nodes (key, value).
        key (str): Key that will be created in the final dict.
        value: Value that will be associated with ``key``.

    Returns:
        A new (key, value) pair with our own formatting rules applied.

    >>> post_parse_node([], 'mynamespace mykey', '')
    ('mykey', '')
    >>> post_parse_node(
    ... [('mynamespace mykey', None)], 'mynamespace mykey', {})
    ('mykey', {'__xmlns__': 'mynamespace'})
    >>> post_parse_node([], 'mykey', 'urn:uuid:abcef')
    ('mykey', 'abcef')
    >>> post_parse_node([], 'mykey', '3.1415')
    ('mykey', 3.1415)
    >>> post_parse_node([], 'mykey', '42.0')
    ('mykey', 42)
    >>> post_parse_node([], 'mykey', None)
    ('mykey', '')
    >>> post_parse_node([], '@namespace attr', 'value')
    ('@namespace attr', 'value')

    """
    # Remove namespace prefix
    # Ignore namespace prefix for attributes
    is_attribute = key.startswith("@")
    tag_split = key.split(ns_sep)
    if not is_attribute and len(tag_split) == 2:
        ns = tag_split[0]
        key = tag_split[1]

        # If ns prefix appear only one time in path we are in the root node of
        # that namespace.
        paths_prefix = [x[0] for x in path]
        found = sum(p.startswith(ns + ns_sep) for p in paths_prefix)
        if found == 1 and isinstance(value, dict):
            value["__xmlns__"] = ns

    # Remove uuid prefix
    try:
        prefix = "urn:uuid:"
        if value.startswith(prefix):
            value = value.replace(prefix, "")
    except AttributeError:
        pass

    # Convert number to proper type
    value = try_convert_number(value)

    # Empty string for empty tags (instead of None)
    value = "" if value is None else value

    return key, value


def post_parse_attr(in_elem, parent_dict={}, parent_key=""):
    """Convert / format attributes in Xmltodict output and returns a new dict.

    Recursively parse input dictionary to format attributes differently
    from Xmltodict rules.

    Rules applied :
     - Replace attributes key (starting with '@') by a new key in the
       parent dict (or in place for list item) with the notation :
       Parent@Attr
     - Replace value key for node with attributes (starting with '#text')
       by a simple string if dict is otherwise empty, or by a new key using
       the parent name

    Args:
        in_elem: Input value.
        parent_dict: Parent dictionary (recursive call only).
        parent_key: Parent key in ``parent_dict`` (recursive call only).

    Returns:
        Newly created dict with attributes converted to our format.

    >>> sorted(
    ...  post_parse_attr({
    ...   'mydict': {'#text': 'mytext', '@attrib': 'myattrib'}
    ...  }).items()
    ... )
    [('mydict', 'mytext'), ('mydict@attrib', 'myattrib')]

    """
    out_elem = {}
    parent_dict = out_elem if parent_dict is None else parent_dict

    if isinstance(in_elem, dict):
        for k, v in in_elem.items():
            if k.startswith("@"):
                attrib_key = "{}@{}".format(parent_key, k[1:])
                parent_dict[attrib_key] = v
            else:
                out_elem[k] = post_parse_attr(v, out_elem, k)

        out_len = len(out_elem.keys())
        if out_len == 0:
            out_elem = ""
        elif "#text" in out_elem and out_len == 1:
            out_elem = out_elem["#text"]
        elif "#text" in out_elem and out_len > 1:
            out_elem[parent_key] = out_elem.pop("#text")
    elif isinstance(in_elem, list):
        out_elem = [post_parse_attr(e, None, parent_key) for e in in_elem]
    else:
        out_elem = in_elem

    return out_elem


def parse_xml(xml_path, namespaces={}, force_list=(), xml_attribs=True):
    """Parse a XML document and returns a dict with proper formating.

    Args:
        xml_path (str): XML file absolute path.
        namespaces (dict): Namespace mapping dict, prefix: namespace. All
            matching namespaces found in the XML document will be processed
            and replaced by prefix.
        force_list (tuple): Tuple containing XML element name that needs
            to appear as list node in the generated dict. This force a list
            even if only one such element is found in a particular XML
            file.
        xml_attribs (boolean): If True, completly ignore all attributes
            found in the XML file.

    Returns:
        A dict representation of the input XML file.

    Raises:
        ValueError: If ``xml_path`` is not a valid file.

    """
    if not os.path.isfile(xml_path):
        raise ValueError("{} is not a file".format(xml_path))

    try:
        with open(xml_path, encoding="utf-8-sig") as file:
            readed_file = file.read()

            # Collapse these namespace
            namespaces = {v: k for k, v in namespaces.items()}

            xml_dict = xmltodict.parse(
                readed_file,
                process_namespaces=True,
                namespaces=namespaces,
                force_list=force_list,
                xml_attribs=xml_attribs,
                postprocessor=post_parse_node,
                dict_constructor=dict,
                namespace_separator=_DEFAULT_NS_SEP,
            )

            if xml_attribs:
                xml_dict = post_parse_attr(xml_dict)

            return xml_dict

    except (Exception, ExpatError) as e:
        get_log().error("Error parsing XML {} : {}".format(xml_path, str(e)))


def validate_xml(xml_path, xsd_id):
    """Validate a XML document with a XSD schema.

    Args:
        xml_path (str): XML file absolute path.
        xsd_id (str): XSD Schema identifier, as found in the catalog file.

    Raises:
        ValueError: If ``xml_path`` is not a valid file.
        LookupError: If XSD Schema could not be found for various raisons.

    """
    if not os.path.isfile(xml_path):
        raise ValueError("{} is not a file".format(xml_path))

    root_path = os.path.dirname(os.path.dirname(__file__))
    catalog_path = os.path.join(root_path, "xsd/catalog.xml")

    # Find schema location using catalog
    catalog = etree.parse(catalog_path).getroot()
    nsmap = {"ns": catalog.nsmap[None]}
    match = catalog.findall(
        ".//ns:public[@publicId='{}']".format(xsd_id), namespaces=nsmap
    )

    if not match:
        raise LookupError("XSD schema not found")
    if len(match) > 1:
        raise LookupError("Multiple XSD schema found")

    xsd_path = os.path.join(root_path, "xsd/{}".format(match[0].attrib["uri"]))

    # Validation
    with modified_dict(os.environ, XML_CATALOG_FILES=catalog_path):
        doc = etree.parse(xml_path)
        schema = etree.XMLSchema(file=xsd_path)
        schema.assertValid(doc)


def canonicalize_xml(xml_path, root=None, ns=None, strip=None):
    """Canonicalize a XML document using C14N method.

    References:
        W3C Canonical XML (v1.1)

    Args:
        xml_path (str): XML file absolute path.
        root (str, optional): New document root (to canonicalize only part
            of the whole XML document).
        ns (str, optional): Namespace associated with `root`.
        strip (str): Element node to strip before canonicalization.

    Returns:
        C14N bytes representation of the XML document.

    Raises:
        ValueError: If ``xml_path`` is not a valid file.
        LookupError: If ``root`` was not found.

    """
    if not os.path.isfile(xml_path):
        raise ValueError("{} is not a file".format(xml_path))

    doc = etree.parse(xml_path)
    nsmap = {"ns": ns}

    if root:
        new_root = doc.getroot().find(".//ns:{}".format(root), namespaces=nsmap)
        if new_root is None:
            raise LookupError("Canonicalization fail, missing root node")

        doc._setroot(new_root)

    if strip:
        etree.strip_elements(doc, strip, with_tail=False)

    bindoc = io.BytesIO()
    doc.write_c14n(bindoc, with_comments=False)

    # In some cases where there is no namespace prefix, write_c14n add lot of
    # 'xmlns=""' attributes that make are not wanted.
    return re.sub(r' xmlns=""', "", bindoc.getvalue().decode("utf-8")).encode("utf-8")
