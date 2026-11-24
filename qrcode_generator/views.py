from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
import qrcode
from django.core.files.base import ContentFile
from .models import QRCodeModel
from .forms import QRCodeForm
from io import BytesIO
from django.http import FileResponse
from edutools_site.file_utils import safe_media_path
from django.contrib.auth.decorators import login_required
import os


@login_required
def generate_qr_code(request):
    if request.method == 'POST':
        if request.POST.get('generate'):
            form = QRCodeForm(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)
                # generate code
                qr = qrcode.make(obj.url)
                qr_code_buffer = BytesIO()
                qr.save(qr_code_buffer, format='PNG')
                obj.image.save('qrcode.png', ContentFile(qr_code_buffer.getvalue()))
                obj.user = request.user
                obj.save()
                return redirect('generate_qr_code')

            return redirect(reverse('generate_qr_code') + '?alert=True')

        elif request.POST.get('delete'):
            obj = QRCodeModel.objects.get(id=request.POST.get('delete'))
            if os.path.exists(str(obj.image.file)) and request.user.id == obj.user.id:
                os.remove(str(obj.image.file))
                obj.delete()
            return redirect('generate_qr_code')

    form = QRCodeForm()
    codes = QRCodeModel.objects.filter(user=request.user).order_by('-id')
    if request.GET.get('alert'):
        alert = True
    else:
        alert = False
    return render(request, "qrcode.html", {'form': form, 'codes': codes, 'alert': alert})


@login_required
def get_qr_image(request, filename):
    # Only the owner may access the QR code; anything else is a 404.
    get_object_or_404(QRCodeModel, image='qr_codes/' + filename, user=request.user)
    attach = bool(request.GET.get('attach'))
    return FileResponse(
        open(safe_media_path('qr_codes', filename), 'rb'),
        as_attachment=attach,
        filename=filename
    )
