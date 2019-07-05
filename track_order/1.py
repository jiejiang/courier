# uncompyle6 version 3.3.5
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.12 (default, Nov 12 2018, 14:36:49) 
# [GCC 5.4.0 20160609]
# Embedded file name: /home/jie/work/django/projects/courier/track_order/parcel_force.py
# Compiled at: 2019-04-24 14:16:37
from PyPDF2 import PdfFileWriter, PdfFileReader
import pdfquery, sys, datetime, re
from lxml import etree
from cStringIO import StringIO
from tempfile import TemporaryFile
from bs4 import BeautifulSoup
bbox_re = re.compile('^\\[(\\d+(?:\\.\\d+)?),\\s(\\d+(?:\\.\\d+)?),\\s(\\d+(?:\\.\\d+)?),\\s(\\d+(?:\\.\\d+)?)\\]$', flags=re.U | re.I)
ref_re = re.compile('^[A-Z0-9]{9,21}$')

def get_position(node):
    if node is None:
        return
    else:
        if 'bbox' not in node.attrib:
            return
        bbox = node.attrib['bbox']
        m = bbox_re.match(bbox.strip())
        if not m:
            return
        return (float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4)))


def valid_reference_number_locations(page_size, ref_pos):
    if not ref_pos or not page_size:
        return False
    if ref_pos[3] / page_size[3] > 0.5:
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
        raise Exception(u'\u9875\u6570\u4e0d\u662f4\u7684\u500d\u6570')
    for package_id in xrange(ret['num_pages'] / 4):
        info = {}
        for i in range(package_id * 4, (package_id + 1) * 4):
            p = infile.getPage(i)
            outfile = PdfFileWriter()
            outfile.addPage(p)
            page_data = StringIO()
            outfile.write(page_data)
            pdf = pdfquery.PDFQuery(page_data)
            pdf.load()
            if 'name' not in info or 'telephone' not in info:
                nodes = pdf.tree.xpath(u"//*[contains(text(), '\u8bf7\u5c0f\u5fc3\u8f7b\u653e')]")
                if len(nodes) > 0:
                    soup = BeautifulSoup(etree.tostring(pdf.tree), 'lxml')
                    segments = filter(lambda x: x, map(lambda x: x.strip(), soup.findAll(text=True)))
                    if len(segments) > 5:
                        name = segments[(-5)]
                        telephone = segments[(-4)]
                        if name and telephone:
                            info['name'] = name
                            info['telephone'] = telephone
            if 'name' not in info or 'telephone' not in info:
                nodes = pdf.tree.xpath("//*[contains(text(), 'Creation Date:')]")
                if len(nodes) > 0:
                    nodes = pdf.tree.xpath("//*[contains(text(), 'Name')]")
                    if len(nodes) > 0:
                        name = nodes[(-1)].text[5:].strip()
                        if name:
                            info['name'] = name
                    nodes = pdf.tree.xpath("//*[contains(text(), 'Phone')]")
                    if len(nodes) > 0:
                        telephone = nodes[(-1)].text[6:].strip()
                        if telephone:
                            info['telephone'] = telephone
            if 'reference_number' not in info or 'dispatch_date' not in info:
                nodes = pdf.tree.xpath("//*[contains(text(), 'CUSTOMS DECLARATION')]")
                if len(nodes) > 0:
                    nodes = pdf.tree.xpath("//*[contains(text(), 'Date of despatch')]")
                    if len(nodes) > 0:
                        dispatch_date = nodes[(-1)].text.replace('Date of despatch', '').strip()
                        if dispatch_date:
                            info['dispatch_date'] = dispatch_date
                    nodes = pdf.tree.xpath("//*[contains(text(), 'Administration of Great Britain')]")
                    if len(nodes) > 0:
                        nodes = nodes[(-1)].getparent().getnext().xpath('./LTTextBoxHorizontal')
                        if len(nodes) > 0:
                            reference_number = nodes[0].text.replace(' ', '').strip()
                            if reference_number:
                                info['reference_number'] = reference_number
            if callback:
                callback((i + 1) * 100.0 / ret['num_pages'])

        for field in ('reference_number', 'name', 'telephone', 'dispatch_date'):
            if not info.get(field, None):
                raise Exception, 'Missing information %s on page %d' % (field, i + 1)

        info['dispatch_date'] = datetime.datetime.strptime(info['dispatch_date'], '%d/%m/%Y')
        order_info.append(info)

    return ret


if __name__ == '__main__':

    def callback(per):
        print >> sys.stderr, per
        sys.stderr.flush()


    with open(sys.argv[1], 'rb') as (f):
        print extract_order_info(f, callback)
# okay decompiling parcel_force.pyc
