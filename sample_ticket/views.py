# *- coding: utf-8 -*

from django.shortcuts import render
import tempfile, shutil, os, sys, zipfile, datetime
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import Http404, StreamingHttpResponse
from wsgiref.util import FileWrapper
from cStringIO import StringIO
from mezzanine.conf import settings

from forms import SampleTicketForm

from tickets import sample_ticket

@method_decorator(staff_member_required(login_url='login'), name='dispatch')
class SampleTicketView(FormView):
    form_class = SampleTicketForm
    template_name = "sample_tickets.html"

    def form_valid(self, form):
        outdir = None
        curdir = os.getcwd()
        try:
            if not self.request.FILES['files']:
                raise Exception, _(u"无上传文件")
            outdir = tempfile.mkdtemp()
            params = {'excel_files' : self.request.FILES.getlist('files'),
                      'outdir': outdir,
                      'debug': settings.DEBUG,
                      'is_jixun': form.cleaned_data['is_jixun']}
            params.update(settings.TICKET_PATHS)

            sample_ticket(**params)

            download_file_obj = StringIO()
            zipf = zipfile.ZipFile(download_file_obj, 'w', zipfile.ZIP_DEFLATED)

            os.chdir(outdir)
            for root, dirs, files in os.walk('.'):
                for file in files:
                    zipf.write(os.path.join(root.decode('utf-8'), file))
            zipf.close()
            file_len = download_file_obj.tell()

            os.chdir(curdir)
            download_file_obj.seek(0)

            chunk_size = 8192
            response = StreamingHttpResponse(FileWrapper(download_file_obj, chunk_size),
                                             content_type='application/octet-stream')
            response['Content-Length'] = file_len
            response['Content-Disposition'] = "attachment; filename=%s" % \
                                              (_(u"小票%s.zip") % datetime.datetime.now().strftime("%Y%m%d%H%M%S"))\
                                                  .encode('utf8')
            return response
        except Exception, inst:
            import traceback
            traceback.print_exc(sys.stderr)
            messages.error(self.request, inst.message)
            return super(SampleTicketView, self).form_invalid(form)
        finally:
            if os.getcwd() <> curdir:
                os.chdir(curdir)
            if outdir:
               shutil.rmtree(outdir)

