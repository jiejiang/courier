# *- coding: utf-8 -*

from PyPDF2 import PdfFileWriter, PdfFileReader
import pdfquery, sys, datetime, re
from lxml import etree
from cStringIO import StringIO
from tempfile import TemporaryFile
from bs4 import BeautifulSoup

bbox_re = re.compile(r"^\[(\d+(?:\.\d+)?),\s(\d+(?:\.\d+)?),\s(\d+(?:\.\d+)?),\s(\d+(?:\.\d+)?)\]$", flags=re.U|re.I)
ref_re = re.compile(r"^[A-Z0-9]{9,21}$")

def get_position(node):
    if node is None:
        return None
    if not 'bbox' in node.attrib:
        return None
    bbox = node.attrib["bbox"]
    m = bbox_re.match(bbox.strip())
    if not m:
        return None
    return (float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4)))

def valid_reference_number_locations(page_size, ref_pos):
    if not ref_pos or not page_size:
        return False
    if ref_pos[3]/page_size[3] > 0.5:
        return False
    return True

def valid_reference_number(reference_number):
    return ref_re.match(reference_number)

def extract_order_info(file_obj, callback=None):
    ret = {'order_info': [], 'num_pages': 0}
    order_info = ret['order_info']
    infile = PdfFileReader(file_obj)
    ret['num_pages'] = infile.getNumPages()
    if ret['num_pages'] % 4 != 0:
        raise Exception(u"页数不是4的倍数")
    for package_id in xrange(ret['num_pages'] / 4):
        info = {}
        for i in range(package_id * 4, (package_id+1) * 4):
            p = infile.getPage(i)
            outfile = PdfFileWriter()
            outfile.addPage(p)
            page_data = StringIO()
            outfile.write(page_data)
            pdf = pdfquery.PDFQuery(page_data)
            pdf.load()
            # print etree.tostring(pdf.tree, pretty_print=True)

            if not 'name' in info or not 'telephone' in info:
                nodes = pdf.tree.xpath(u"//*[contains(text(), '请小心轻放')]")
                if len(nodes) > 0:
                    soup = BeautifulSoup(etree.tostring(pdf.tree), 'lxml')
                    segments = filter(lambda x:x, map(lambda x:x.strip(), soup.findAll(text=True)))
                    if len(segments) > 5:
                        name = segments[-5]
                        telephone = segments[-4]
                        if name and telephone:
                            info['name'] = name
                            info['telephone'] = telephone
            if not 'name' in info or not 'telephone' in info:
                nodes = pdf.tree.xpath("//*[contains(text(), 'Creation Date:')]")
                if len(nodes) > 0:
                    nodes = pdf.tree.xpath("//*[contains(text(), 'Name')]")
                    if len(nodes) > 0:
                        name = nodes[-1].text[5:].strip()
                        if name:
                            info['name'] = name
                    nodes = pdf.tree.xpath("//*[contains(text(), 'Phone')]")
                    if len(nodes) > 0:
                        telephone = nodes[-1].text[6:].strip()
                        if telephone:
                            info['telephone'] = telephone

            if not 'reference_number' in info or not 'dispatch_date' in info:
                nodes = pdf.tree.xpath("//*[contains(text(), 'CUSTOMS DECLARATION')]")
                if len(nodes) > 0:
                    nodes = pdf.tree.xpath("//*[contains(text(), 'Date of despatch')]")
                    if len(nodes) > 0:
                        dispatch_date = nodes[-1].text.replace('Date of despatch', '').strip()
                        if dispatch_date:
                            info['dispatch_date'] = dispatch_date

                    nodes = pdf.tree.xpath("//*[contains(text(), 'Administration of Great Britain')]")
                    if len(nodes) > 0:
                        nodes = nodes[-1].getparent().getnext().xpath("./LTTextBoxHorizontal")
                        if len(nodes) > 0:
                            reference_number = nodes[0].text.replace(' ', '').strip()
                            if reference_number:
                                info['reference_number'] = reference_number

            if callback:
                callback((i+1) * 100. / ret['num_pages'])

        for field in ('reference_number', 'name', 'telephone', 'dispatch_date'):
            if not info.get(field, None):
                raise Exception, "Missing information %s on page %d" % (field, i+1)

        #print info, info['name']

        info['dispatch_date'] = datetime.datetime.strptime(info['dispatch_date'], '%d/%m/%Y')
        order_info.append(info)

    return ret


if __name__ == "__main__":
    def callback(per):
        print >> sys.stderr, per
        sys.stderr.flush()

    with open(sys.argv[1], 'rb') as f:
        print extract_order_info(f, callback)

